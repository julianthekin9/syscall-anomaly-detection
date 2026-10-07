"""Калібрування методів оцінювання аномальності (calib/holdout за записами) і їх порівняння.

Методи (--methods): nll (NLL + квантиль вікна), topk (ранг + квантиль вікна), run_nll і run_rank
(серія аномальних викликів). Для кожного — свої два параметри на calib, підсумок на holdout;
поділ, бутстреп-ресемпли й методика вибору точки спільні.

Критерій вибору робочої точки (--objective, можна кілька): fbeta (за замовчуванням F1), fbeta_prevalence
(F-beta, перерахований на --prevalence), recall_at_fpr (максимум recall при FPR(calib) <= --max_fpr).
--max_fpr разом із fbeta-критеріями — обмеження: кожне значення дає окремий блок результатів.
Захист від виродження: точку, не кращу за «тривогу на кожне вікно», позначено degenerate.
Порівняння без вибору точки: pAUC при FPR <= 5% на holdout.

Usage:
    hids-calibrate --service PHP_CWE-434
    hids-calibrate --config configs/php_cwe_434.yaml --service PHP_CWE-434 --objective fbeta --objective recall_at_fpr --max_fpr 0.01 0.05
    hids-calibrate --service PHP_CWE-434 --methods nll run_nll --beta 2
    hids-calibrate --service FIXT --checkpoint tests/golden/FIXT.pt --dataset_root tests/golden/data --val_step 32
"""

import csv
import hashlib
import json
import logging
import math
import os
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
import torch
from sklearn.metrics import precision_recall_curve, roc_auc_score, roc_curve
from torch.utils.data import DataLoader

from syscall_hids.data.datasets import SequenceDataset
from syscall_hids.data.layout import recording_files, test_recording_files
from syscall_hids.data.parsing import read_recording
from syscall_hids.data.sequences import encode_recording, make_sequences
from syscall_hids.modules.models import SyscallLSTM
from syscall_hids.modules.scoring import compute_step_scores
from syscall_hids.tools import resource_guard
from syscall_hids.tools.arg_parser import _add_bool, _add_dir_args, _add_ram_args, _new_parser
from syscall_hids.tools.arg_parser_tools import check_args
from syscall_hids.tools.calibration import (
    METHOD_NAMES,
    OBJECTIVE_KINDS,
    PAUC_MAX_FPR,
    Method,
    Objective,
    aggregate,
    bootstrap_auc,
    bootstrap_metrics,
    bootstrap_record_metrics,
    bootstrap_samples,
    build_methods,
    build_objectives,
    ci95,
    ci95_summary,
    confusion_at_threshold,
    curve_scores,
    default_p_grid,
    edge_flags,
    fbeta,
    is_degenerate,
    metrics_from_confusion,
    objective_grid,
    paired_delta_ci,
    pauc,
    precision_at_prevalence,
    record_flags,
    record_metrics,
    select_curve_param,
    smooth_select,
    split_recordings,
    step_ranks,
    trivial_fbeta,
    window_starts,
)
from syscall_hids.tools.checkpoint import checkpoint_features, load_model
from syscall_hids.tools.utils import get_git_commit

Q_GRID_DEFAULT = [0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.99, 1.0]
M_GRID_DEFAULT = list(range(1, 33))
SANITY_REL_TOL = 1e-4  # відносна розбіжність порогу, вище якої — попередження
SANITY_REL_FAIL = 0.01  # вище — зупинка (якщо не --ignore_sanity)
CACHE_VERSION = 3  # 2: ранги на кроках (val_rank, test_rank); 3: час кінця вікна test_t_end
MIN_BOOTSTRAP_RECORDINGS = 5  # менше записів класу в holdout — інтервали бутстрепу ненадійні
DEGENERATE_MARGIN = 0.01  # F-beta має бути вище тривіального рівня більш ніж на це значення
REFERENCE_METHOD = "nll"
BASELINE_LABEL = "Базова лінія (параметри з чекпоінта)"
TRIVIAL_LABEL = "Тривога на кожне вікно"
DEGENERATE_WARNING = "degenerate: не краще за тривогу на все вікна"
METHOD_COLORS = {"nll": "#2563eb", "topk": "#dc2626", "run_nll": "#16a34a", "run_rank": "#9333ea"}


def build_calibrate_arg_parser(description: str | None = None):
    """Парсер hids-calibrate. Невідомі ключі YAML ігноруються: можна передати конфіг навчання."""
    parser = _new_parser(ignore_unknown_config_file_keys=True, description=description)
    group = parser.add_argument_group("Data and model")
    group.add_argument("--service", required=True, help="Scenario name (dataset subdirectory)")
    group.add_argument("--checkpoint", default=None, help="Path to the .pt (default: {model_dir}/<service>.pt)")
    group.add_argument("--dataset_root", type=str, default="./DATASET_LIDDS", help="Dataset root")
    group.add_argument("--val_step", type=int, default=None,
                       help="Validation window step (default: train_args.seq_step from the checkpoint)")
    group.add_argument("--baseline_p", type=float, default=99.0,
                       help="Threshold percentile of the checkpoint if it has no train_args (old checkpoints)")
    group.add_argument("--batch_size", type=int, default=32, help="Inference batch size")
    group.add_argument("--device", type=str, default=None, help="torch device (default: cuda if available, else cpu)")

    group = parser.add_argument_group("Calibration")
    group.add_argument("--methods", nargs="+", choices=METHOD_NAMES, default=list(METHOD_NAMES),
                       help="Scoring methods to calibrate and compare")
    group.add_argument("--objective", action="append", choices=OBJECTIVE_KINDS, default=None,
                       help="Operating point criterion; repeat for several (default: fbeta)")
    group.add_argument("--max_fpr", type=float, nargs="+", default=None,
                       help="FPR(calib) limits: a constraint for fbeta criteria (one block each, plus the "
                            "unconstrained one) and the limit of recall_at_fpr (default for it: 0.01 0.05)")
    group.add_argument("--calib_fraction", type=float, default=0.5, help="Share of test recordings in the calib part")
    # окреме ім'я замість --seed: seed зі збережених конфігів навчання не впливає на поділ
    group.add_argument("--split_seed", type=int, default=0, help="Seed for the calib/holdout split and the bootstrap")
    group.add_argument("--q_grid", type=float, nargs="+", default=Q_GRID_DEFAULT,
                       help="Window aggregation quantiles (nll, topk)")
    _add_bool(group, "--include_mean", True, "Add window_agg=mean as a separate grid row (nll, topk)")
    group.add_argument("--m_grid", type=int, nargs="+", default=M_GRID_DEFAULT,
                       help="Minimal anomalous run lengths (run_nll, run_rank); values > seq_len are dropped")
    group.add_argument("--p_grid", type=float, nargs="+", default=None,
                       help="Threshold percentiles (default: 90-99 step 0.5, 99.1-99.9 step 0.1, 99.9-99.999 log)")
    group.add_argument("--beta", type=float, default=1.0, help="beta of F-beta")
    group.add_argument("--prevalence", type=float, default=0.01, help="Realistic attack share for the precision rescale")
    group.add_argument("--bootstrap", type=int, default=1000, help="Bootstrap resamples on holdout (0: off)")
    _add_bool(group, "--ignore_sanity", False, "Continue even if the recomputed checkpoint threshold differs by > 1%%")

    group = parser.add_argument_group("Output")
    group.add_argument("--out_dir", type=str, default=None, help="Output directory (None -> {work_dir}/calibration/<service>)")
    _add_bool(group, "--no_cache", False, "Ignore and overwrite the per-step score cache")
    _add_bool(group, "--write_checkpoint", False,
              "Save a calibrated copy {model_dir}/<service>_f2.pt (nll, first --objective block)")

    _add_dir_args(parser, model_dir=True)
    _add_ram_args(parser)
    return parser


def _check_calibrate_args(parser, args) -> None:
    if not all(0 < q <= 1 for q in args.q_grid):
        parser.error("--q_grid: every value must satisfy 0 < q <= 1")
    if not all(m >= 1 for m in args.m_grid):
        parser.error("--m_grid: every value must be >= 1")
    if not 0 < args.calib_fraction < 1:
        parser.error("--calib_fraction must satisfy 0 < calib_fraction < 1")
    if args.p_grid is not None and not all(0 < p < 100 for p in args.p_grid):
        parser.error("--p_grid: every value must satisfy 0 < p < 100")
    if args.max_fpr is not None and not all(0 < f < 1 for f in args.max_fpr):
        parser.error("--max_fpr: every value must satisfy 0 < max_fpr < 1")
    if not 0 < args.prevalence < 1:
        parser.error("--prevalence must satisfy 0 < prevalence < 1")
    if args.beta <= 0:
        parser.error("--beta must be > 0")
    if args.bootstrap < 0:
        parser.error("--bootstrap must be >= 0")
    if args.write_checkpoint and REFERENCE_METHOD not in args.methods:
        parser.error("--write_checkpoint requires nll in --methods (inference supports only nll)")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def data_fingerprint(files: list[Path], dataset_root: str) -> str:
    """sha256 від відсортованого списку «відносний шлях, розмір, mtime» усіх використаних записів."""
    entries = []
    for path in files:
        st = path.stat()
        entries.append(f"{path.relative_to(dataset_root).as_posix()},{st.st_size},{st.st_mtime_ns}")
    return hashlib.sha256("\n".join(sorted(entries)).encode("utf-8")).hexdigest()


def _checkpoint_agg(checkpoint: dict) -> float | str:
    """Агрегація з чекпоінта в термінах aggregate(): max — це квантиль 1.0."""
    if checkpoint["window_agg"] == "max":
        return 1.0
    if checkpoint["window_agg"] == "mean":
        return "mean"
    return float(checkpoint["window_agg_quantile"])


def _row_label(q: float | str) -> dict:
    return {"window_agg": "mean", "q": None} if q == "mean" else {"window_agg": "quantile", "q": float(q)}


def _param_label(method: Method, value) -> dict:
    return _row_label(value) if method.family == "quantile" else {"m": int(value)}


def _param_text(method: Method, value) -> str:
    if method.family == "run":
        return f"m={int(value)}"
    return "mean" if value == "mean" else f"q={value:g}"


def _fname(beta: float) -> str:
    return f"F{beta:g}"


def recording_step_scores(
    model: SyscallLSTM, checkpoint: dict, path: Path, step: int, device: torch.device, batch_size: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    """NLL (float32), ранг справжнього виклику (int32) на кожному кроці [n_windows, seq_len] з одного проходу
    моделі і час останньої строки кожного вікна від початку файлу в секундах (float32 [n_windows]);
    None, якщо вікон немає.

    Нарізка та сама, що в build_*_sequences: read_recording -> encode_recording -> make_sequences.
    Позиції вікон для часу — window_starts (та сама формула, що в make_sequences, звірено тестом).
    """
    seq_len = checkpoint["seq_len"]
    lines = read_recording(str(path))
    if len(lines) < seq_len + 1:
        return None
    rows = encode_recording(checkpoint["vocabs"], lines, *checkpoint_features(checkpoint))
    X, y = make_sequences(rows, seq_len, step)
    if not len(X):
        return None
    starts = window_starts(len(lines), seq_len, step)
    if len(starts) != len(X):
        raise RuntimeError(f"{path}: window_starts gives {len(starts)} windows, make_sequences {len(X)}")
    ts = np.fromiter((line.timestamp for line in lines), dtype=np.float64, count=len(lines))
    t_end = (ts[starts + seq_len] - ts[0]).astype(np.float32)
    nll_parts: list[np.ndarray] = []
    rank_parts: list[np.ndarray] = []
    with torch.no_grad():
        for x, y_batch in DataLoader(SequenceDataset(X, y), batch_size=batch_size, shuffle=False):
            y_batch = y_batch.to(device)
            logits = model(x.to(device))
            nll_parts.append(compute_step_scores(logits, y_batch).cpu().numpy().astype(np.float32))
            rank_parts.append(step_ranks(logits, y_batch[..., 0]).cpu().numpy())
    return np.concatenate(nll_parts, axis=0), np.concatenate(rank_parts, axis=0), t_end


def compute_cache(
    model: SyscallLSTM, checkpoint: dict, args, val_files: list[Path], normal_files: list[Path],
    abnormal_files: list[Path], val_step: int, device: torch.device,
) -> dict[str, np.ndarray]:
    """Один прохід моделі по val і test: NLL і ранги на кроках, мітки вікон, індекс записи й час кінця вікна test."""
    seq_len = checkpoint["seq_len"]
    every = args.ram_check_every_n_recordings

    val_nll: list[np.ndarray] = []
    val_rank: list[np.ndarray] = []
    for i, path in enumerate(val_files):
        scores = recording_step_scores(model, checkpoint, path, val_step, device, args.batch_size)
        if scores is not None:
            val_nll.append(scores[0])
            val_rank.append(scores[1])
        if (i + 1) % every == 0:
            resource_guard.check_ram(f"{args.service}/val: after {i + 1} recordings")

    test_nll: list[np.ndarray] = []
    test_rank: list[np.ndarray] = []
    test_t_end: list[np.ndarray] = []
    rec_idx_parts: list[np.ndarray] = []
    rec_files: list[str] = []
    rec_is_attack: list[bool] = []
    for group, files in ((False, normal_files), (True, abnormal_files)):
        for i, path in enumerate(files):
            scores = recording_step_scores(model, checkpoint, path, seq_len, device, args.batch_size)
            if scores is not None:
                rec_idx_parts.append(np.full(len(scores[0]), len(rec_files), dtype=np.int32))
                test_nll.append(scores[0])
                test_rank.append(scores[1])
                test_t_end.append(scores[2])
                rec_files.append(path.relative_to(args.dataset_root).as_posix())
                rec_is_attack.append(group)
            if (i + 1) % every == 0:
                resource_guard.check_ram(f"{args.service}/test: after {i + 1} recordings")

    if not val_nll or not test_nll:
        raise ValueError(f"[{args.service}] val or test split has no windows of length {seq_len + 1}")

    rec_is_attack_arr = np.array(rec_is_attack, dtype=bool)
    rec_idx = np.concatenate(rec_idx_parts)
    return {
        "val_nll": np.concatenate(val_nll),
        "val_rank": np.concatenate(val_rank),
        "test_nll": np.concatenate(test_nll),
        "test_rank": np.concatenate(test_rank),
        "test_t_end": np.concatenate(test_t_end),
        "test_rec_idx": rec_idx,
        "test_is_attack": rec_is_attack_arr[rec_idx],
        "test_files": np.array(rec_files),
        "test_rec_is_attack": rec_is_attack_arr,
    }


def load_or_compute_cache(cache_path: str, key: dict, compute) -> tuple[dict[str, np.ndarray], bool]:
    if os.path.exists(cache_path):
        with np.load(cache_path, allow_pickle=False) as cached:
            if all(k in cached and str(cached[k]) == str(v) for k, v in key.items()):
                return {k: cached[k] for k in cached.files if k not in key}, True
    data = compute()
    np.savez(cache_path, **data, **{k: np.array(v) for k, v in key.items()})
    return data, False


def point_metrics(scores: np.ndarray, is_attack: np.ndarray, threshold: float, beta: float) -> dict:
    conf = confusion_at_threshold(scores, is_attack, [threshold])
    metrics = metrics_from_confusion(conf["tp"], conf["fp"], conf["fn"], conf["tn"], beta)
    out = {k: int(v[0]) for k, v in conf.items()}
    out.update({k: float(v[0]) for k, v in metrics.items()})
    return out


def sanity_check(val_nll: np.ndarray, checkpoint: dict, baseline_p: float, ignore_sanity: bool) -> dict:
    """Перерахунок порогу чекпоінта з кешу val: перевірка, що нарізка й NLL ті самі, що в навчанні."""
    expected = float(checkpoint["threshold"])
    recomputed = float(np.percentile(aggregate(val_nll, _checkpoint_agg(checkpoint)), baseline_p))
    rel_diff = abs(recomputed - expected) / max(abs(expected), 1e-12)
    match = rel_diff <= SANITY_REL_TOL
    if not match:
        logging.warning(
            f"WARNING: recomputed checkpoint threshold {recomputed:.6f} != checkpoint threshold {expected:.6f} "
            f"(relative difference {rel_diff:.2e})"
        )
        if rel_diff > SANITY_REL_FAIL and not ignore_sanity:
            raise SystemExit(
                f"Sanity check failed: threshold differs by {rel_diff:.2%} > {SANITY_REL_FAIL:.0%}. "
                f"Check --val_step / --baseline_p or pass --ignore_sanity."
            )
    return {
        "threshold_checkpoint": expected, "threshold_recomputed": recomputed, "p": baseline_p,
        "rel_diff": rel_diff, "threshold_match": bool(match),
    }


def _objective_label_uk(objective: Objective, beta: float, prevalence: float) -> str:
    """Підпис значення критерію (кольорова шкала теплової карти)."""
    if objective.kind == "fbeta":
        return f"{_fname(beta)} на калібрувальній частині"
    if objective.kind == "fbeta_prevalence":
        return f"{_fname(beta)} при частці атак {prevalence:g} на калібрувальній частині"
    return "Повнота (recall) на калібрувальній частині"


def _objective_title_uk(objective: Objective, beta: float) -> str:
    base = {"fbeta": f"максимум {_fname(beta)}", "fbeta_prevalence": f"максимум {_fname(beta)} при реальній частці атак",
            "recall_at_fpr": "максимум повноти"}[objective.kind]
    return base + ("" if objective.max_fpr is None else f", FPR ≤ {objective.max_fpr:g}")


def _heatmap_name(objective: Objective, beta: float) -> str:
    if objective.kind == "recall_at_fpr":
        return "recall_heatmap.png"
    suffix = "_prevalence" if objective.kind == "fbeta_prevalence" else ""
    return f"f{beta:g}{suffix}_heatmap.png"


def _log_edges(share: np.ndarray) -> np.ndarray:
    """Межі клітинок по осі «частка вище порогу» (лог-шкала): геометричні середини сусідніх значень."""
    mids = np.sqrt(share[:-1] * share[1:])
    first = share[0] ** 2 / mids[0] if len(mids) else share[0] * 1.2
    last = share[-1] ** 2 / mids[-1] if len(mids) else share[-1] / 1.2
    return np.concatenate([[first], mids, [last]])


def plot_heatmap(
    method: Method, objective: Objective, values: np.ndarray, rows: list, p_grid: np.ndarray, selection,
    fpr_grid: np.ndarray, beta: float, prevalence: float, out_path: str,
) -> None:
    """Теплова карта критерію: X — частка val вище порогу (100 − p, %) у лог-шкалі, Y — параметр вікна."""
    share = 100.0 - np.asarray(p_grid, dtype=np.float64)
    order = np.argsort(share)[::-1]  # частка спадає зліва направо = поріг росте
    share, vals, fpr = share[order], values[:, order], fpr_grid[:, order]
    edges_x = _log_edges(share)
    edges_y = np.arange(len(rows) + 1) - 0.5
    fig, ax = plt.subplots(figsize=(11, 5 if len(rows) <= 12 else 8))
    mesh = ax.pcolormesh(edges_x, edges_y, vals, cmap="viridis", shading="flat")
    ax.set_xscale("log")
    ax.set_xlim(edges_x[0], edges_x[-1])  # спадна вісь: поріг росте вправо
    cbar = fig.colorbar(mesh, ax=ax)
    cbar.set_label(_objective_label_uk(objective, beta, prevalence))
    extra: list = []
    if objective.max_fpr is not None:
        # недопустимі клітинки затінено (контур інтерполював би між сходинками й брехав)
        blocked = np.ma.masked_where(fpr <= objective.max_fpr, np.ones_like(fpr))
        ax.pcolormesh(edges_x, edges_y, blocked, cmap=ListedColormap(["#ffffff"]), alpha=0.6, shading="flat")
        extra.append(Patch(facecolor="#ffffff", alpha=0.6, edgecolor="#9ca3af",
                           label=f"Недопустимо: FPR > {objective.max_fpr:g} (calib)"))
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(["середнє" if q == "mean" else f"{q:g}" for q in rows], fontsize=8 if len(rows) > 12 else None)
    if selection is not None:
        (si, sj), (ri, rj), _ = selection
        pos = {int(j): k for k, j in enumerate(order)}
        point = f"({method.row_param}*, {method.col_param}*)"
        ax.scatter([share[pos[rj]]], [ri], marker="x", s=90, color="#dc2626", linewidths=2, label="Сирий максимум")
        ax.scatter([share[pos[sj]]], [si], marker="*", s=220, color="white", edgecolors="black",
                   linewidths=1, label=f"Обрана точка {point}")
    unit = "вікон" if method.family == "quantile" else "кроків"
    ax.set_xlabel(f"Частка {unit} вище порогу на валідації, %")
    ax.set_ylabel(method.row_axis)
    title = method.title.format(f=_fname(beta) if objective.kind != "recall_at_fpr" else "повноти")
    ax.set_title(f"{title}\nКритерій: {_objective_title_uk(objective, beta)}")
    # легенда під графіком, щоб не закривати обрану точку
    handles = ax.get_legend_handles_labels()[0] + extra
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=8, facecolor="#e5e7eb")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_pr_curve(
    method: Method, is_attack: np.ndarray, scores: np.ndarray, selected: dict, baseline: dict | None, out_path: str
) -> None:
    precision, recall, _ = precision_recall_curve(is_attack, scores)
    point = f"({method.row_param}*, {method.col_param}*)"
    curve = "Крива для q*" if method.family == "quantile" else "Крива для p* (оцінка вікна — довжина серії)"
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.plot(recall, precision, color=METHOD_COLORS[method.name], label=curve)
    ax.scatter([selected["recall"]], [selected["precision"]], marker="*", s=200, color="#dc2626",
               edgecolors="black", zorder=3, label=f"Робоча точка {point}")
    if baseline is not None:
        ax.scatter([baseline["recall"]], [baseline["precision"]], marker="o", s=60, color="#16a34a",
                   edgecolors="black", zorder=3, label="Базова лінія (чекпоінт)")
    ax.set_xlabel("Повнота (recall)")
    ax.set_ylabel("Точність (precision)")
    ax.set_xlim(0, 1.02)
    ax.set_ylim(0, 1.02)
    ax.set_title(f"Крива точність–повнота на відкладеній частині\n{method.label}")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_fbeta_comparison(block: dict, beta: float, out_path: str) -> None:
    """F-beta на holdout по методах з 95% ДІ; лінії базової лінії й тривіального рівня."""
    entries = block["methods"]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    x = np.arange(len(entries))
    for i, e in enumerate(entries):
        if e["infeasible"]:
            ax.text(i, 0.02, "недосяжно", ha="center", va="bottom", rotation=90, fontsize=9, color="#6b7280")
            continue
        h = e["holdout"]
        ci = h.get("ci95")
        yerr = None if ci is None else np.clip([[h["fbeta"] - ci["fbeta"][0]], [ci["fbeta"][1] - h["fbeta"]]], 0, None)
        ax.bar(i, h["fbeta"], yerr=yerr, capsize=6, color=METHOD_COLORS[e["method"]], alpha=0.85,
               hatch="//" if e["degenerate"] else None, edgecolor="black" if e["degenerate"] else None)
    extra: list = []
    ax.axhline(block["baseline"]["holdout"]["fbeta"], color="black", linestyle="--", linewidth=1.2, label=BASELINE_LABEL)
    ax.axhline(block["trivial"]["holdout"]["fbeta"], color="#dc2626", linestyle=":", linewidth=1.5, label=TRIVIAL_LABEL)
    if any(e["degenerate"] for e in entries):
        extra.append(Patch(facecolor="white", hatch="//", edgecolor="black",
                           label="Вироджена точка (не краще за тривогу на все)"))
    ax.set_xticks(x)
    ax.set_xticklabels([textwrap.fill(e["label"], 18) for e in entries])
    ax.set_ylabel(f"{_fname(beta)} на відкладеній частині")
    ax.set_ylim(0, 1.02)
    ax.set_title(f"Порівняння методів оцінювання аномальності\nКритерій: {_objective_title_uk(Objective(block['objective'], block['max_fpr']), beta)}")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(handles=ax.get_legend_handles_labels()[0] + extra, loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_pr_comparison(entries: list[dict], curves: dict, is_attack: np.ndarray, out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    for e in entries:
        if e["method"] not in curves:
            continue
        color = METHOD_COLORS[e["method"]]
        precision, recall, _ = precision_recall_curve(is_attack, curves[e["method"]])
        ax.plot(recall, precision, color=color, label=e["label"])
        ax.scatter([e["holdout"]["recall"]], [e["holdout"]["precision"]], marker="*", s=200, color=color,
                   edgecolors="black", zorder=3)
    ax.scatter([], [], marker="*", s=200, color="white", edgecolors="black", label="Робочі точки")
    ax.set_xlabel("Повнота (recall)")
    ax.set_ylabel("Точність (precision)")
    ax.set_xlim(0, 1.02)
    ax.set_ylim(0, 1.02)
    ax.set_title("Криві точність–повнота на відкладеній частині")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_roc_comparison(threshold_free: list[dict], curves: dict, is_attack: np.ndarray, out_path: str) -> None:
    """ROC на holdout для параметра кривої, обраного на calib за pAUC; AUC і pAUC у легенді."""
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    for e in threshold_free:
        fpr, tpr, _ = roc_curve(is_attack, curves[e["method"]])
        ax.plot(fpr, tpr, color=METHOD_COLORS[e["method"]],
                label=f"{e['label']} (AUC = {e['roc_auc']:.3f}, pAUC@{PAUC_MAX_FPR:g} = {e['pauc']:.3f})")
    ax.axvline(PAUC_MAX_FPR, color="gray", linestyle="--", linewidth=1)
    ax.plot([0, 1], [0, 1], color="gray", linestyle=":", linewidth=1)
    ax.set_xlabel("Частка хибних тривог (FPR)")
    ax.set_ylabel("Частка виявлених атак (TPR)")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.set_title("ROC-криві методів на відкладеній частині")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_recall_at_fpr(blocks: list[dict], out_path: str) -> None:
    """Повнота на holdout при обмеженнях FPR(calib), згрупована за max_fpr; над стовпцем — FPR(holdout)."""
    blocks = [b for b in blocks if b["objective"] == "recall_at_fpr"]
    methods = [e["method"] for e in blocks[0]["methods"]]
    labels = {e["method"]: e["label"] for e in blocks[0]["methods"]}
    width = 0.8 / len(methods)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for k, name in enumerate(methods):
        for g, block in enumerate(blocks):
            e = next(x for x in block["methods"] if x["method"] == name)
            xpos = g - 0.4 + width * (k + 0.5)
            if e["infeasible"]:
                ax.text(xpos, 0.02, "недосяжно", ha="center", va="bottom", rotation=90, fontsize=8, color="#6b7280")
                continue
            h = e["holdout"]
            ci = h.get("ci95")
            yerr = None if ci is None else np.clip([[h["recall"] - ci["recall"][0]], [ci["recall"][1] - h["recall"]]], 0, None)
            ax.bar(xpos, h["recall"], width=width, yerr=yerr, capsize=4, color=METHOD_COLORS[name], alpha=0.85,
                   label=labels[name] if g == 0 else None)
            ax.text(xpos, min(h["recall"] + 0.04, 0.98), f"FPR {h['fpr']:.3f}", ha="center", fontsize=7, rotation=90)
    ax.set_xticks(range(len(blocks)))
    ax.set_xticklabels([f"FPR ≤ {b['max_fpr']:g}" for b in blocks])
    ax.set_xlabel("Обмеження частки хибних тривог на калібрувальній частині")
    ax.set_ylabel("Повнота (recall) на відкладеній частині")
    ax.set_ylim(0, 1.05)
    ax.set_title("Повнота за обмеження частки хибних тривог")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _fmt_ci(ci: dict | None, key: str) -> str:
    return "" if ci is None or ci.get(key) is None else f"[{ci[key][0]:.3f}, {ci[key][1]:.3f}]"


def log_nll_baseline_table(result: dict, beta: float) -> None:
    """nll: базова лінія (чекпоінт) проти каліброваної точки."""
    f = _fname(beta)
    base, sel = result["metrics"]["holdout"]["baseline"], result["metrics"]["holdout"]["selected"]
    bq, sq = result["baseline"], result["selected"]

    def agg_name(d: dict) -> str:
        return "mean" if d["window_agg"] == "mean" else f"q={d['q']:g}"

    rows = [
        ("window agg", agg_name(bq), agg_name(sq)),
        ("percentile p", f"{bq['p']:g}", f"{sq['p']:g}"),
        ("threshold", f"{bq['threshold']:.4f}", f"{sq['threshold']:.4f}"),
        ("TP / FP", f"{base['tp']} / {base['fp']}", f"{sel['tp']} / {sel['fp']}"),
        ("FN / TN", f"{base['fn']} / {base['tn']}", f"{sel['fn']} / {sel['tn']}"),
        ("precision", f"{base['precision']:.4f}", f"{sel['precision']:.4f}"),
        ("recall (TPR)", f"{base['recall']:.4f}", f"{sel['recall']:.4f}"),
        ("FPR", f"{base['fpr']:.4f}", f"{sel['fpr']:.4f}"),
        (f, f"{base['fbeta']:.4f}", f"{sel['fbeta']:.4f}"),
        ("ROC-AUC", f"{base['roc_auc']:.4f}", f"{sel['roc_auc']:.4f}"),
    ]
    if "ci95" in sel:
        rows += [
            (f"{f} 95% CI", _fmt_ci(base["ci95"], "fbeta"), _fmt_ci(sel["ci95"], "fbeta")),
            ("recall 95% CI", _fmt_ci(base["ci95"], "recall"), _fmt_ci(sel["ci95"], "recall")),
            ("FPR 95% CI", _fmt_ci(base["ci95"], "fpr"), _fmt_ci(sel["ci95"], "fpr")),
        ]
    logging.info(f"\n[nll/{result['objective']['tag']}] Holdout: baseline (checkpoint) vs calibrated, "
                 f"attack window share pi = {result['attack_fraction_holdout']:.4f}")
    logging.info(f"{'':<16}{'baseline':>20}{'calibrated':>20}")
    for name, b, s in rows:
        logging.info(f"{name:<16}{b:>20}{s:>20}")


def log_block_table(block: dict, beta: float, prevalence: float) -> None:
    """Таблиця блоку критерію: обрана точка кожного методу на calib і holdout, тривіальний рівень, записи."""
    f = _fname(beta)
    logging.info(f"\n[{block['tag']}] holdout, attack window share pi = {block['attack_fraction_holdout']:.4f}; "
                 f"* = degenerate (not better than alarm on every window); {f}@pi rescaled to prevalence={prevalence:g}")
    logging.info(f"{'method':<10}{'params':<20}{'rec_cal':>8}{'fpr_cal':>8}{'recall':>8}{'FPR':>8}{'prec':>8}"
                 f"{f:>9}{f'{f} 95% CI':>18}{f'{f}@pi':>8}{'trivial':>8}{'att_rec':>8}{'nrm_rec':>8}{'delay_s':>9}"
                 f"{'d'+f+' vs nll':>13}{'sig':>5}")
    t = block["trivial"]
    logging.info(f"{'trivial':<10}{'alarm on all':<20}{1.0:>8.4f}{1.0:>8.4f}{1.0:>8.4f}{1.0:>8.4f}"
                 f"{t['holdout']['precision']:>8.4f}{t['holdout']['fbeta']:>9.4f}{'':>18}{t['holdout']['fbeta_prevalence']:>8.4f}"
                 f"{t['holdout']['fbeta']:>8.4f}{1.0:>8.4f}{1.0:>8.4f}{'':>9}{'':>13}{'':>5}")
    b = block["baseline"]["holdout"]
    logging.info(f"{'baseline':<10}{block['baseline']['params']:<20}{'':>8}{'':>8}{b['recall']:>8.4f}{b['fpr']:>8.4f}"
                 f"{b['precision']:>8.4f}{b['fbeta']:>9.4f}{_fmt_ci(b.get('ci95'), 'fbeta'):>18}"
                 f"{block['baseline']['prevalence_rescaled']['fbeta']:>8.4f}{t['holdout']['fbeta']:>8.4f}")
    for e in block["methods"]:
        if e["infeasible"]:
            logging.info(f"{e['method']:<10}{'infeasible':<20}")
            continue
        h, c, r, d = e["holdout"], e["calib"], e["record_metrics"], e["delta_fbeta_vs_nll"]
        value = ("*" if e["degenerate"] else "") + f"{h['fbeta']:.4f}"
        delay = "" if r["median_delay_sec"] is None else f"{r['median_delay_sec']:.2f}"
        dv = "" if d is None else f"{d['value']:+.4f}"
        sig = "" if d is None or d["ci95"] is None else ("yes" if d["significant"] else "no")
        logging.info(
            f"{e['method']:<10}{e['params_text']:<20}{c['recall']:>8.4f}{c['fpr']:>8.4f}{h['recall']:>8.4f}{h['fpr']:>8.4f}"
            f"{h['precision']:>8.4f}{value:>9}"
            f"{_fmt_ci(h.get('ci95'), 'fbeta'):>18}{e['prevalence_rescaled']['fbeta']:>8.4f}{e['trivial_fbeta']['holdout']:>8.4f}"
            f"{r['attack_detected']:>8.3f}{r['normal_alarmed']:>8.3f}{delay:>9}{dv:>13}{sig:>5}"
        )


def log_threshold_free_table(threshold_free: list[dict]) -> None:
    logging.info(f"\nThreshold-free comparison on holdout (curve parameter chosen on calib by pAUC@{PAUC_MAX_FPR:g}, "
                 f"McClish standardization):")
    logging.info(f"{'method':<10}{'curve param':<14}{'pAUC':>8}{'pAUC 95% CI':>18}{'ROC-AUC':>9}{'dpAUC vs nll':>14}"
                 f"{'dpAUC 95% CI':>20}{'sig':>5}")
    for e in threshold_free:
        d = e["delta_pauc_vs_nll"]
        dv = "" if d is None else f"{d['value']:+.4f}"
        dci = "" if d is None or d["ci95"] is None else f"[{d['ci95'][0]:+.3f}, {d['ci95'][1]:+.3f}]"
        sig = "" if d is None or d["ci95"] is None else ("yes" if d["significant"] else "no")
        ci = "" if e["pauc_ci95"] is None else f"[{e['pauc_ci95'][0]:.3f}, {e['pauc_ci95'][1]:.3f}]"
        logging.info(f"{e['method']:<10}{e['param_text']:<14}{e['pauc']:>8.4f}{ci:>18}{e['roc_auc']:>9.4f}{dv:>14}{dci:>20}{sig:>5}")


def write_grid_csv(
    path: str, method: Method, grid: dict, rows: list, p_grid: np.ndarray, score: np.ndarray,
    smoothed: np.ndarray | None, feasible: np.ndarray | None, prevalence: float, beta: float,
) -> None:
    """Сітка calib: параметри, поріг (θ або τ; k_eff для рангів), метрики, F-beta@prevalence, критерій і його згладження."""
    metric_cols = ["tp", "fp", "fn", "tn", "precision", "recall", "fpr", "f1", "fbeta"]
    with_k = method.step_key == "rank"
    fbeta_prev = fbeta(precision_at_prevalence(grid["recall"], grid["fpr"], prevalence), grid["recall"], beta)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        head = ["window_agg", "q", "p", "threshold"] if method.family == "quantile" else ["m", "p", "tau"]
        writer.writerow([*head, *(["k_eff"] if with_k else []), *metric_cols, "fbeta_prevalence",
                         "score", "score_smoothed", "feasible"])
        for i, row in enumerate(rows):
            if method.family == "quantile":
                label = _row_label(row)
                key = [label["window_agg"], "" if label["q"] is None else f"{label['q']:g}"]
            else:
                key = [int(row)]
            for j, p in enumerate(p_grid):
                thr = grid["threshold"][i, j].item()
                writer.writerow([
                    *key, f"{p:g}", thr, *([math.floor(thr)] if with_k else []),
                    *[grid[c][i, j].item() for c in metric_cols], fbeta_prev[i, j].item(), score[i, j].item(),
                    "" if smoothed is None else smoothed[i, j].item(),
                    True if feasible is None else bool(feasible[i, j]),
                ])


def _point(method: Method, rows: list, p_grid: np.ndarray, grid: dict, score: np.ndarray, ij: tuple[int, int]) -> dict:
    """Опис точки сітки: параметри, поріг (θ або τ), k_eff для рангів, F-beta і значення критерію на calib."""
    i, j = ij
    thr = float(grid["threshold"][i, j])
    out = {**_param_label(method, rows[i]), "p": float(p_grid[j])}
    out["threshold" if method.family == "quantile" else "tau"] = thr
    if method.step_key == "rank":
        out["k_eff"] = math.floor(thr)
    if method.family == "run":
        out["rule"] = "R >= m"
    out["fbeta"] = float(grid["fbeta"][i, j])
    out["fpr_calib"] = float(grid["fpr"][i, j])
    out["score"] = float(score[i, j])
    return out


def evaluate_holdout(scores: np.ndarray, threshold: float, ctx: dict, beta: float) -> tuple[dict, dict | None]:
    """Метрики holdout (+ ROC-AUC) і, якщо бутстреп увімкнено, метрики на спільних ресемплах та 95% ДІ."""
    mask, is_attack = ctx["holdout_mask"], ctx["test_is_attack"]
    m = point_metrics(scores[mask], is_attack[mask], threshold, beta)
    m["roc_auc"] = float(roc_auc_score(is_attack[mask], scores[mask]))
    boot = None
    if ctx["sample"] is not None:
        boot = bootstrap_metrics(scores, is_attack, ctx["test_rec_idx"], ctx["holdout_order"], threshold, ctx["sample"], beta)
        m["ci95"] = ci95_summary(boot)
    return m, boot


def evaluate_records(scores: np.ndarray, threshold: float, ctx: dict) -> dict:
    """Метрики на рівні записів holdout для робочої точки (+ 95% ДІ на спільних ресемплах)."""
    alarmed, attack, delay = record_flags(
        scores > threshold, ctx["test_is_attack"], ctx["test_rec_idx"], ctx["test_t_end"], ctx["holdout_order"]
    )
    out = record_metrics(alarmed, attack, delay)
    out["ci95"] = None if ctx["sample"] is None else bootstrap_record_metrics(alarmed, attack, delay, ctx["sample"])
    return out


def _rescaled(m: dict, prevalence: float, beta: float) -> dict:
    precision = float(precision_at_prevalence(m["recall"], m["fpr"], prevalence))
    return {"precision": precision, "recall": m["recall"], "fbeta": float(fbeta(precision, m["recall"], beta))}


def calibrate_block(
    method: Method, objective: Objective, grid: dict, rows: list, p_grid: np.ndarray, ctx: dict, common: dict, args
) -> dict:
    """Вибір точки за критерієм на calib, метрики calib/holdout, перевірка виродження, файли {out_dir}/{tag}/{метод}/."""
    beta, prevalence = args.beta, args.prevalence
    val_steps, test_steps = ctx["steps"][method.step_key]
    calib_mask, holdout_mask, test_is_attack = ctx["calib_mask"], ctx["holdout_mask"], ctx["test_is_attack"]
    is_ref = method.name == REFERENCE_METHOD
    name = f"{method.name}/{objective.tag}"

    score, feasible, tiebreak = objective_grid(grid, objective, beta, prevalence)
    mean_row = rows.index("mean") if "mean" in rows else None
    selection = smooth_select(score, mean_row, feasible, tiebreak)
    method_dir = os.path.join(ctx["out_dir"], objective.tag, method.name)
    os.makedirs(method_dir, exist_ok=True)

    pi_calib, pi_holdout = ctx["pi_calib"], ctx["pi_holdout"]
    trivial = {"calib": trivial_fbeta(pi_calib, beta), "holdout": trivial_fbeta(pi_holdout, beta),
               "prevalence": trivial_fbeta(prevalence, beta)}
    result = {
        "method": method.name,
        "label": method.label,
        "row_param": method.row_param,
        "col_param": method.col_param,
        "step_score": method.step_key,
        "objective": {"kind": objective.kind, "max_fpr": objective.max_fpr, "tag": objective.tag},
        "beta": beta,
        **common,
        "trivial_fbeta": trivial,
    }
    summary = {"method": method.name, "label": method.label, "row_param": method.row_param, "col_param": method.col_param,
               "infeasible": selection is None, "trivial_fbeta": trivial}

    if selection is None:
        logging.warning(f"WARNING: [{name}] infeasible: no grid point with FPR(calib) <= {objective.max_fpr:g}")
        result.update({"infeasible": True, "selected": None, "raw_max": None, "degenerate": None, "metrics": None})
        plot_heatmap(method, objective, score, rows, p_grid, None, grid["fpr"], beta, prevalence,
                     os.path.join(method_dir, _heatmap_name(objective, beta)))
        write_grid_csv(os.path.join(method_dir, "grid.csv"), method, grid, rows, p_grid, score, None, feasible, prevalence, beta)
        with open(os.path.join(method_dir, "calibration.json"), "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, ensure_ascii=False)
        summary.update({"degenerate": None, "selected": None, "params_text": "infeasible", "holdout": None, "calib": None,
                        "record_metrics": None, "prevalence_rescaled": None, "_boot": None, "_scores": None, "_result": result})
        return summary

    (si, sj), (ri, rj), smoothed = selection
    on_edge = edge_flags((si, sj), score.shape, mean_row)
    if on_edge["row"] or on_edge["col"]:
        axes = " and ".join(n for n, flag in ((method.row_param, on_edge["row"]), ("p", on_edge["col"])) if flag)
        logging.warning(f"WARNING: [{name}] selected point is on the grid edge ({axes}): consider widening the grid")

    sel_row, sel_p = rows[si], float(p_grid[sj])
    scores, sel_threshold = method.operating_point(val_steps, test_steps, sel_row, sel_p)

    named = [("selected", scores, sel_threshold)]
    if is_ref:
        named.append(("baseline", ctx["baseline_scores"], ctx["baseline_threshold"]))
    metrics: dict = {"calib": {}, "holdout": {}}
    boots: dict = {}
    for n, sc, thr in named:
        metrics["calib"][n] = point_metrics(sc[calib_mask], test_is_attack[calib_mask], thr, beta)
    for n, sc, thr in named:
        metrics["holdout"][n], boots[n] = evaluate_holdout(sc, thr, ctx, beta)
    rescaled = {"prevalence": prevalence}
    for n, _, _ in named:
        rescaled[n] = _rescaled(metrics["holdout"][n], prevalence, beta)
    records = evaluate_records(scores, sel_threshold, ctx)

    cal, hold = metrics["calib"]["selected"], metrics["holdout"]["selected"]
    if objective.kind == "fbeta_prevalence":
        value_calib, level_calib = _rescaled(cal, prevalence, beta)["fbeta"], trivial["prevalence"]
        value_hold, level_hold = rescaled["selected"]["fbeta"], trivial["prevalence"]
    else:
        value_calib, level_calib = cal["fbeta"], trivial["calib"]
        value_hold, level_hold = hold["fbeta"], trivial["holdout"]
    degenerate = is_degenerate(cal["fpr"], value_calib, level_calib, DEGENERATE_MARGIN)
    degenerate_holdout = is_degenerate(hold["fpr"], value_hold, level_hold, DEGENERATE_MARGIN)
    if degenerate:
        logging.warning(f"WARNING: [{name}] {DEGENERATE_WARNING} (FPR calib={cal['fpr']:.3f}, "
                        f"{_fname(beta)}={value_calib:.4f}, trivial={level_calib:.4f})")

    selected = {**_point(method, rows, p_grid, grid, score, (si, sj)), "score_smoothed": float(smoothed[si, sj]),
                "on_edge": on_edge}
    grid_desc = {"p": [float(p) for p in p_grid], "beta": beta}
    if method.family == "quantile":
        grid_desc = {"q": [float(q) for q in args.q_grid], "include_mean": bool(args.include_mean), **grid_desc,
                     "smoothing": "3x3 mean over feasible neighbours (grid indices); mean row along p only"}
    else:
        grid_desc = {"m": [int(m) for m in rows], **grid_desc, "p_kind": "percentile of all val step scores",
                     "smoothing": "3x3 mean over feasible neighbours (grid indices)"}
    result.update({
        "infeasible": False,
        "degenerate": degenerate,
        "degenerate_holdout": degenerate_holdout,
        "grid": grid_desc,
        "selected": selected,
        "raw_max": _point(method, rows, p_grid, grid, score, (ri, rj)),
        "baseline": ctx["baseline_desc"] if is_ref else None,
        "metrics": metrics,
        "record_metrics": records,
        "attack_fraction_holdout": pi_holdout,
        "prevalence_rescaled": rescaled,
    })
    if is_ref:
        result["sanity"] = ctx["sanity"]

    with open(os.path.join(method_dir, "calibration.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
    write_grid_csv(os.path.join(method_dir, "grid.csv"), method, grid, rows, p_grid, score, smoothed, feasible, prevalence, beta)
    plot_heatmap(method, objective, score, rows, p_grid, selection, grid["fpr"], beta, prevalence,
                 os.path.join(method_dir, _heatmap_name(objective, beta)))
    plot_pr_curve(method, test_is_attack[holdout_mask], scores[holdout_mask], hold,
                  metrics["holdout"].get("baseline"), os.path.join(method_dir, "pr_curve_holdout.png"))
    if is_ref:
        log_nll_baseline_table(result, beta)
    raw = result["raw_max"]
    logging.info(
        f"[{name}] selected: {_param_text(method, sel_row)} p={sel_p:g} "
        f"{'threshold' if method.family == 'quantile' else 'tau'}={grid['threshold'][si, sj]:.4f}"
        f"{' k_eff=' + str(selected['k_eff']) if 'k_eff' in selected else ''} FPR(calib)={cal['fpr']:.4f}; "
        f"raw max: {_param_text(method, rows[ri])} p={raw['p']:g} score={raw['score']:.4f}"
    )

    summary.update({
        "degenerate": degenerate,
        "degenerate_holdout": degenerate_holdout,
        "params_text": f"{_param_text(method, sel_row)} p={sel_p:g}",
        "selected": {k: v for k, v in selected.items() if k not in ("score", "score_smoothed", "fbeta")},
        "calib": {"recall": cal["recall"], "fpr": cal["fpr"], "fbeta": cal["fbeta"], "score": selected["score"],
                  "score_smoothed": selected["score_smoothed"]},
        "holdout": hold,
        "prevalence_rescaled": rescaled["selected"],
        "record_metrics": records,
        "calibration_json": f"{objective.tag}/{method.name}/calibration.json",
        "_boot": boots["selected"],
        "_scores": scores[holdout_mask],
        "_result": result,
    })
    return summary


def threshold_free_comparison(method: Method, rows: list, p_grid: np.ndarray, ctx: dict) -> dict:
    """Параметр кривої за pAUC на calib, pAUC і ROC-AUC на holdout, бутстреп pAUC на спільних ресемплах."""
    val_steps, test_steps = ctx["steps"][method.step_key]
    calib_mask, holdout_mask, is_attack = ctx["calib_mask"], ctx["holdout_mask"], ctx["test_is_attack"]
    param, pauc_calib = select_curve_param(method, val_steps, test_steps[calib_mask], is_attack[calib_mask], rows, p_grid)
    scores = curve_scores(method, val_steps, test_steps, param)
    hold = scores[holdout_mask]
    boot = None
    if ctx["sample"] is not None:
        boot = bootstrap_auc(scores, is_attack, ctx["test_rec_idx"], ctx["holdout_order"], ctx["sample"])
    param_text = (f"q={param:g}" if param != "mean" else "mean") if method.family == "quantile" else f"p_step={param:g}"
    return {
        "method": method.name,
        "label": method.label,
        "curve_param": {"name": "q" if method.family == "quantile" else "p_step",
                        "value": param if param == "mean" else float(param)},
        "param_text": param_text,
        "pauc_calib": pauc_calib,
        "pauc": pauc(is_attack[holdout_mask], hold),
        "roc_auc": float(roc_auc_score(is_attack[holdout_mask], hold)),
        "pauc_ci95": None if boot is None else ci95(boot),
        "_boot": boot,
        "_scores": hold,
    }


def _delta(value: float, ref_value: float, boot, ref_boot) -> dict:
    d = {"value": value - ref_value, "ci95": None, "significant": None}
    if boot is not None and ref_boot is not None:
        d.update(paired_delta_ci(boot, ref_boot))
    return d


def build_block(objective: Objective, summaries: list[dict], baseline: dict, trivial: dict, threshold_free: list[dict],
                common: dict, ctx: dict, args) -> dict:
    """Блок одного критерію: Δ F-beta до nll, comparison.json, графіки порівняння, таблиця в консолі."""
    ref = next((s for s in summaries if s["method"] == REFERENCE_METHOD and not s["infeasible"]), None)
    for s in summaries:
        if ref is None or s["infeasible"]:
            s["delta_fbeta_vs_nll"] = None
            continue
        s["delta_fbeta_vs_nll"] = _delta(
            s["holdout"]["fbeta"], ref["holdout"]["fbeta"],
            None if s["_boot"] is None else s["_boot"]["fbeta"], None if ref["_boot"] is None else ref["_boot"]["fbeta"],
        )
    block = {
        "objective": objective.kind,
        "max_fpr": objective.max_fpr,
        "tag": objective.tag,
        "beta": args.beta,
        "attack_fraction_holdout": ctx["pi_holdout"],
        "trivial": trivial,
        "baseline": baseline,
        "methods": [{k: v for k, v in s.items() if not k.startswith("_")} for s in summaries],
    }
    out = os.path.join(ctx["out_dir"], objective.tag, "comparison")
    os.makedirs(out, exist_ok=True)
    comparison = {
        **{k: common[k] for k in ("service", "checkpoint", "git_commit", "data_fingerprint", "split_seed",
                                  "calib_fraction", "windows")},
        "prevalence": args.prevalence,
        "split": {part: {k: v for k, v in common["split"][part].items() if k.startswith("n_")}
                  for part in ("calib", "holdout")},
        "bootstrap": {"n": args.bootstrap, "seed": args.split_seed, "unit": "recording", "stratified": True,
                      "shared_resamples": True} if args.bootstrap else None,
        "reference_method": REFERENCE_METHOD if ref is not None else None,
        "degenerate_rule": f"FPR(calib) > 0.5 or F-beta(calib) <= trivial + {DEGENERATE_MARGIN}",
        **block,
        "threshold_free": [{k: v for k, v in e.items() if not k.startswith("_")} for e in threshold_free],
    }
    with open(os.path.join(out, "comparison.json"), "w", encoding="utf-8") as fh:
        json.dump(comparison, fh, indent=2, ensure_ascii=False)
    is_attack = ctx["test_is_attack"][ctx["holdout_mask"]]
    curves = {s["method"]: s["_scores"] for s in summaries if not s["infeasible"]}
    plot_fbeta_comparison(block, args.beta, os.path.join(out, f"f{args.beta:g}_comparison.png"))
    plot_pr_comparison([e for e in block["methods"] if not e["infeasible"]], curves, is_attack,
                       os.path.join(out, "pr_comparison.png"))
    plot_roc_comparison(threshold_free, {e["method"]: e["_scores"] for e in threshold_free}, is_attack,
                        os.path.join(out, "roc_comparison.png"))
    log_block_table(block, args.beta, args.prevalence)
    return block


CSV_COLUMNS = [
    "objective", "beta", "max_fpr", "method", "label", "params", "infeasible", "degenerate", "degenerate_holdout",
    "recall_calib", "fpr_calib", "fbeta_calib", "recall", "recall_lo", "recall_hi", "fpr", "fpr_lo", "fpr_hi",
    "precision", "fbeta", "fbeta_lo", "fbeta_hi", "fbeta_prevalence", "trivial_fbeta",
    "pauc_0.05", "pauc_lo", "pauc_hi", "roc_auc",
    "attack_detected", "attack_detected_lo", "attack_detected_hi", "normal_alarmed", "normal_alarmed_lo",
    "normal_alarmed_hi", "median_delay_sec", "median_delay_lo", "median_delay_hi",
    "delta_fbeta_vs_nll", "delta_fbeta_lo", "delta_fbeta_hi", "delta_fbeta_significant",
    "delta_pauc_vs_nll", "delta_pauc_lo", "delta_pauc_hi", "delta_pauc_significant",
]


def _ci_pair(ci: dict | None, key: str) -> list:
    return ["", ""] if ci is None or ci.get(key) is None else list(ci[key])


def write_comparison_csv(path: str, blocks: list[dict], threshold_free: list[dict]) -> None:
    """Усі блоки критеріїв: рядок на (блок, метод) + baseline і trivial; pAUC — з порівняння без вибору точки."""
    tf = {e["method"]: e for e in threshold_free}
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for block in blocks:
            head = {"objective": block["objective"], "beta": block["beta"],
                    "max_fpr": "" if block["max_fpr"] is None else block["max_fpr"]}
            t = block["trivial"]
            writer.writerow({**head, "method": "trivial", "label": TRIVIAL_LABEL, "params": "alarm on all",
                             "recall": 1.0, "fpr": 1.0, "precision": t["holdout"]["precision"],
                             "fbeta": t["holdout"]["fbeta"], "fbeta_prevalence": t["holdout"]["fbeta_prevalence"],
                             "trivial_fbeta": t["holdout"]["fbeta"], "attack_detected": 1.0, "normal_alarmed": 1.0})
            b = block["baseline"]
            bh = b["holdout"]
            writer.writerow({**head, "method": "baseline", "label": b["label"], "params": b["params"],
                             "recall": bh["recall"], **dict(zip(("recall_lo", "recall_hi"), _ci_pair(bh.get("ci95"), "recall"))),
                             "fpr": bh["fpr"], **dict(zip(("fpr_lo", "fpr_hi"), _ci_pair(bh.get("ci95"), "fpr"))),
                             "precision": bh["precision"], "fbeta": bh["fbeta"],
                             **dict(zip(("fbeta_lo", "fbeta_hi"), _ci_pair(bh.get("ci95"), "fbeta"))),
                             "fbeta_prevalence": b["prevalence_rescaled"]["fbeta"], "trivial_fbeta": t["holdout"]["fbeta"],
                             "roc_auc": bh["roc_auc"]})
            for e in block["methods"]:
                row = {**head, "method": e["method"], "label": e["label"], "params": e["params_text"],
                       "infeasible": e["infeasible"], "trivial_fbeta": e["trivial_fbeta"]["holdout"]}
                f = tf.get(e["method"])
                if f is not None:
                    row.update({"pauc_0.05": f["pauc"], "roc_auc": f["roc_auc"],
                                **dict(zip(("pauc_lo", "pauc_hi"), f["pauc_ci95"] or ["", ""]))})
                    if f["delta_pauc_vs_nll"] is not None:
                        d = f["delta_pauc_vs_nll"]
                        row.update({"delta_pauc_vs_nll": d["value"], "delta_pauc_significant": d["significant"],
                                    **dict(zip(("delta_pauc_lo", "delta_pauc_hi"), d["ci95"] or ["", ""]))})
                if not e["infeasible"]:
                    h, c, r = e["holdout"], e["calib"], e["record_metrics"]
                    rci = r["ci95"] or {}
                    row.update({
                        "degenerate": e["degenerate"], "degenerate_holdout": e["degenerate_holdout"],
                        "recall_calib": c["recall"], "fpr_calib": c["fpr"], "fbeta_calib": c["fbeta"],
                        "recall": h["recall"], **dict(zip(("recall_lo", "recall_hi"), _ci_pair(h.get("ci95"), "recall"))),
                        "fpr": h["fpr"], **dict(zip(("fpr_lo", "fpr_hi"), _ci_pair(h.get("ci95"), "fpr"))),
                        "precision": h["precision"], "fbeta": h["fbeta"],
                        **dict(zip(("fbeta_lo", "fbeta_hi"), _ci_pair(h.get("ci95"), "fbeta"))),
                        "fbeta_prevalence": e["prevalence_rescaled"]["fbeta"],
                        "attack_detected": r["attack_detected"], "normal_alarmed": r["normal_alarmed"],
                        "median_delay_sec": "" if r["median_delay_sec"] is None else r["median_delay_sec"],
                        **dict(zip(("attack_detected_lo", "attack_detected_hi"), _ci_pair(rci, "attack_detected"))),
                        **dict(zip(("normal_alarmed_lo", "normal_alarmed_hi"), _ci_pair(rci, "normal_alarmed"))),
                        **dict(zip(("median_delay_lo", "median_delay_hi"), _ci_pair(rci, "median_delay_sec"))),
                    })
                    d = e["delta_fbeta_vs_nll"]
                    if d is not None:
                        row.update({"delta_fbeta_vs_nll": d["value"], "delta_fbeta_significant": d["significant"],
                                    **dict(zip(("delta_fbeta_lo", "delta_fbeta_hi"), d["ci95"] or ["", ""]))})
                writer.writerow(row)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = build_calibrate_arg_parser(description=__doc__)
    args = parser.parse_args()
    _check_calibrate_args(parser, args)
    args, input_log_messages = check_args(args)
    for message, level in input_log_messages:
        logging.log(level, message)
    resource_guard.configure(
        args.ram_guard_enabled, args.ram_soft_limit_percent, args.ram_hard_limit_percent, args.ram_throttle_sleep_sec
    )
    out_dir = args.out_dir or os.path.join(args.work_dir, "calibration", args.service)
    os.makedirs(out_dir, exist_ok=True)
    beta = args.beta

    device = torch.device(args.device or ("cuda" if torch.cuda.is_available() else "cpu"))
    checkpoint_path = Path(args.checkpoint or os.path.join(args.model_dir, f"{args.service}.pt"))
    model, checkpoint = load_model(checkpoint_path.stem, device, str(checkpoint_path.parent))
    train_args = checkpoint.get("train_args") or {}
    val_step = args.val_step or train_args.get("seq_step")
    if val_step is None:
        parser.error("checkpoint has no train_args.seq_step: pass --val_step (the seq_step used in training)")
    baseline_p = float(train_args.get("threshold_percentile", args.baseline_p))
    seq_len = checkpoint["seq_len"]

    val_files = recording_files(args.service, "val", args.dataset_root)
    normal_files, abnormal_files = test_recording_files(args.service, args.dataset_root)
    fingerprint = data_fingerprint(val_files + normal_files + abnormal_files, args.dataset_root)
    checkpoint_sha256 = sha256_file(str(checkpoint_path))
    cache_key = {
        "cache_version": CACHE_VERSION, "checkpoint_sha256": checkpoint_sha256,
        "val_step": int(val_step), "seq_len": int(seq_len), "data_fingerprint": fingerprint,
    }
    cache_path = os.path.join(out_dir, f"cache_{args.service}.npz")
    if args.no_cache and os.path.exists(cache_path):
        os.remove(cache_path)
    cache, from_cache = load_or_compute_cache(
        cache_path, cache_key,
        lambda: compute_cache(model, checkpoint, args, val_files, normal_files, abnormal_files, val_step, device),
    )
    logging.info(f"Per-step NLL and ranks {'loaded from cache' if from_cache else 'computed and cached'}: {cache_path}")
    val_nll, test_nll = cache["val_nll"], cache["test_nll"]
    test_is_attack, test_rec_idx = cache["test_is_attack"], cache["test_rec_idx"]
    test_files, rec_is_attack = cache["test_files"], cache["test_rec_is_attack"]
    logging.info(
        f"val windows: {len(val_nll)} (step {val_step}), test windows: {len(test_nll)} "
        f"({int(test_is_attack.sum())} attack) from {len(test_files)} recordings"
    )

    sanity = sanity_check(val_nll, checkpoint, baseline_p, args.ignore_sanity)

    # один поділ і одні бутстреп-ресемпли для всіх методів і критеріїв
    calib_recs, holdout_recs = split_recordings(rec_is_attack, args.calib_fraction, args.split_seed)
    calib_mask = np.isin(test_rec_idx, calib_recs)
    holdout_mask = ~calib_mask
    if test_is_attack[holdout_mask].all() or not test_is_attack[holdout_mask].any():
        raise SystemExit("holdout has only one window class: need at least 2 normal and 2 abnormal recordings")
    holdout_normal = holdout_recs[~rec_is_attack[holdout_recs]]
    holdout_abnormal = holdout_recs[rec_is_attack[holdout_recs]]
    sample = (bootstrap_samples(len(holdout_normal), len(holdout_abnormal), args.bootstrap, args.split_seed)
              if args.bootstrap else None)
    if sample is not None and min(len(holdout_normal), len(holdout_abnormal)) < MIN_BOOTSTRAP_RECORDINGS:
        logging.warning(
            f"WARNING: holdout has {len(holdout_normal)} normal / {len(holdout_abnormal)} abnormal recordings: "
            f"bootstrap intervals and delta significance are unreliable (< {MIN_BOOTSTRAP_RECORDINGS} per class)"
        )

    p_grid = default_p_grid() if args.p_grid is None else np.round(np.sort(np.asarray(args.p_grid, dtype=np.float64)), 6)
    q_rows: list = list(args.q_grid) + (["mean"] if args.include_mean else [])
    m_rows = [m for m in args.m_grid if m <= seq_len]
    if len(m_rows) < len(args.m_grid):
        logging.info(f"--m_grid: values > seq_len={seq_len} dropped (a window has only {seq_len} steps)")
    methods = build_methods(args.methods)
    if any(m.family == "run" for m in methods) and not m_rows:
        parser.error(f"--m_grid has no values <= seq_len={seq_len}")
    objectives = build_objectives(args.objective or ["fbeta"], args.max_fpr)

    def files_of(recs: np.ndarray) -> dict:
        part_mask = np.isin(test_rec_idx, recs)
        normal = [str(test_files[r]) for r in recs if not rec_is_attack[r]]
        abnormal = [str(test_files[r]) for r in recs if rec_is_attack[r]]
        return {
            "normal": normal,
            "abnormal": abnormal,
            "n_windows": int(part_mask.sum()),
            "n_attack_windows": int(test_is_attack[part_mask].sum()),
            "n_normal": len(normal),
            "n_abnormal": len(abnormal),
        }

    common = {
        "service": args.service,
        "checkpoint": {"path": str(checkpoint_path), "sha256": checkpoint_sha256},
        "git_commit": get_git_commit(),
        "split_seed": args.split_seed,
        "calib_fraction": args.calib_fraction,
        "dataset_root": str(args.dataset_root),
        "data_fingerprint": fingerprint,
        "windows": {"seq_len": int(seq_len), "test_step": int(seq_len), "val_step": int(val_step), "n_val_windows": int(len(val_nll))},
        "split": {"calib": files_of(calib_recs), "holdout": files_of(holdout_recs)},
    }

    base_q = _checkpoint_agg(checkpoint)
    ctx = {
        "out_dir": out_dir,
        "steps": {"nll": (val_nll, test_nll), "rank": (cache["val_rank"], cache["test_rank"])},
        "test_is_attack": test_is_attack,
        "test_rec_idx": test_rec_idx,
        "test_t_end": cache["test_t_end"],
        "calib_mask": calib_mask,
        "holdout_mask": holdout_mask,
        "holdout_order": np.concatenate([holdout_normal, holdout_abnormal]),
        "sample": sample,
        "pi_calib": float(test_is_attack[calib_mask].mean()),
        "pi_holdout": float(test_is_attack[holdout_mask].mean()),
        "sanity": sanity,
        "baseline_scores": aggregate(test_nll, base_q),
        "baseline_threshold": float(checkpoint["threshold"]),
        "baseline_desc": {**_row_label(base_q), "p": baseline_p,
                          "p_source": "train_args" if "threshold_percentile" in train_args else "--baseline_p",
                          "threshold": float(checkpoint["threshold"]), "checkpoint_window_agg": checkpoint["window_agg"]},
    }

    # базова лінія (чекпоінт, NLL) і тривіальний детектор не залежать від критерію
    base_holdout, _ = evaluate_holdout(ctx["baseline_scores"], ctx["baseline_threshold"], ctx, beta)
    baseline = {
        "label": BASELINE_LABEL, **_row_label(base_q), "p": baseline_p, "threshold": ctx["baseline_threshold"],
        "holdout": base_holdout, "prevalence_rescaled": _rescaled(base_holdout, args.prevalence, beta),
        "params": f"{'mean' if base_q == 'mean' else f'q={base_q:g}'} p={baseline_p:g}",
    }
    trivial = {part: {"precision": pi, "recall": 1.0, "fpr": 1.0, "fbeta": trivial_fbeta(pi, beta),
                      "fbeta_prevalence": trivial_fbeta(args.prevalence, beta)}
               for part, pi in (("calib", ctx["pi_calib"]), ("holdout", ctx["pi_holdout"]))}

    # сітка calib і порівняння без вибору точки — один раз на метод
    rows_of = {m.name: q_rows if m.family == "quantile" else m_rows for m in methods}
    grids = {}
    threshold_free = []
    for m in methods:
        val_steps, test_steps = ctx["steps"][m.step_key]
        grids[m.name] = m.search(val_steps, test_steps[calib_mask], test_is_attack[calib_mask], rows_of[m.name], p_grid, beta)
        threshold_free.append(threshold_free_comparison(m, rows_of[m.name], p_grid, ctx))
    ref_tf = next((e for e in threshold_free if e["method"] == REFERENCE_METHOD), None)
    for e in threshold_free:
        e["delta_pauc_vs_nll"] = None if ref_tf is None else _delta(e["pauc"], ref_tf["pauc"], e["_boot"], ref_tf["_boot"])
    if ref_tf is None:
        logging.info(f"{REFERENCE_METHOD} is not in --methods: paired deltas vs {REFERENCE_METHOD} are not computed")

    blocks = []
    nll_results = {}
    for objective in objectives:
        summaries = [calibrate_block(m, objective, grids[m.name], rows_of[m.name], p_grid, ctx, common, args) for m in methods]
        nll_results[objective.tag] = next((s["_result"] for s in summaries if s["method"] == REFERENCE_METHOD), None)
        blocks.append(build_block(objective, summaries, baseline, trivial, threshold_free, common, ctx, args))

    write_comparison_csv(os.path.join(out_dir, "comparison.csv"), blocks, threshold_free)
    if any(b["objective"] == "recall_at_fpr" for b in blocks):
        plot_recall_at_fpr(blocks, os.path.join(out_dir, "recall_at_fpr.png"))
    log_threshold_free_table(threshold_free)
    logging.info(f"Results: {out_dir}")

    if args.write_checkpoint:
        first = objectives[0].tag
        nll_result = nll_results[first]
        if len(methods) > 1 or len(objectives) > 1:
            logging.info(f"--write_checkpoint: only nll from the first criterion block ({first}) is written "
                         f"(inference supports only nll); other results stay in their calibration.json")
        if nll_result is None or nll_result["infeasible"]:
            raise SystemExit(f"--write_checkpoint: nll has no feasible point in block {first}")
        sel = nll_result["selected"]
        out_ckpt = Path(args.model_dir) / f"{args.service}_f2.pt"
        if out_ckpt.resolve() == checkpoint_path.resolve():
            raise SystemExit(f"Refusing to overwrite the source checkpoint {checkpoint_path}")
        calibrated = dict(checkpoint)
        calibrated["window_agg"] = sel["window_agg"]
        if sel["window_agg"] != "mean":
            calibrated["window_agg_quantile"] = float(sel["q"])
        calibrated["threshold"] = sel["threshold"]
        calibrated["calibration"] = nll_result
        os.makedirs(out_ckpt.parent, exist_ok=True)
        torch.save(calibrated, out_ckpt)
        logging.info(f"Calibrated checkpoint copy: {out_ckpt}")


if __name__ == "__main__":
    main()
