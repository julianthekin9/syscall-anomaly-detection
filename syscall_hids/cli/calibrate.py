"""Калібрування методів оцінювання аномальності під F2 (calib/holdout за записами) і їх порівняння.

Методи (--methods): nll (NLL + квантиль вікна), topk (ранг + квантиль вікна), run_nll і run_rank
(серія аномальних викликів). Для кожного — свої два параметри на calib, підсумок на holdout;
поділ, бутстреп-ресемпли й методика вибору точки спільні.

Usage:
    hids-calibrate --service PHP_CWE-434
    hids-calibrate --config configs/php_cwe_434.yaml --service PHP_CWE-434 --write_checkpoint
    hids-calibrate --service PHP_CWE-434 --methods nll run_nll
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
    Method,
    aggregate,
    bootstrap_metrics,
    bootstrap_samples,
    build_methods,
    ci95_summary,
    confusion_at_threshold,
    edge_flags,
    fbeta,
    metrics_from_confusion,
    paired_delta_ci,
    precision_at_prevalence,
    smooth_select,
    split_recordings,
    step_ranks,
)
from syscall_hids.tools.checkpoint import checkpoint_features, load_model
from syscall_hids.tools.utils import get_git_commit

Q_GRID_DEFAULT = [0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.99, 1.0]
M_GRID_DEFAULT = list(range(1, 33))
SANITY_REL_TOL = 1e-4  # відносна розбіжність порогу, вище якої — попередження
SANITY_REL_FAIL = 0.01  # вище — зупинка (якщо не --ignore_sanity)
CACHE_VERSION = 2  # 2: додано ранги на кроках (val_rank, test_rank)
MIN_BOOTSTRAP_RECORDINGS = 5  # менше записів класу в holdout — інтервали бутстрепу ненадійні
REFERENCE_METHOD = "nll"
BASELINE_LABEL = "Базова лінія (параметри з чекпоінта)"
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
    group.add_argument("--calib_fraction", type=float, default=0.5, help="Share of test recordings in the calib part")
    # окреме ім'я замість --seed: seed зі збережених конфігів навчання не впливає на поділ
    group.add_argument("--split_seed", type=int, default=0, help="Seed for the calib/holdout split and the bootstrap")
    group.add_argument("--q_grid", type=float, nargs="+", default=Q_GRID_DEFAULT,
                       help="Window aggregation quantiles (nll, topk)")
    _add_bool(group, "--include_mean", True, "Add window_agg=mean as a separate grid row (nll, topk)")
    group.add_argument("--m_grid", type=int, nargs="+", default=M_GRID_DEFAULT,
                       help="Minimal anomalous run lengths (run_nll, run_rank); values > seq_len are dropped")
    group.add_argument("--p_grid_min", type=float, default=90.0, help="Smallest threshold percentile")
    group.add_argument("--p_grid_max", type=float, default=99.9, help="Largest threshold percentile")
    group.add_argument("--p_grid_step", type=float, default=0.1, help="Threshold percentile step")
    group.add_argument("--beta", type=float, default=2.0, help="beta of F-beta")
    group.add_argument("--prevalence", type=float, default=0.01, help="Realistic attack share for the precision rescale")
    group.add_argument("--bootstrap", type=int, default=1000, help="Bootstrap resamples on holdout (0: off)")
    _add_bool(group, "--ignore_sanity", False, "Continue even if the recomputed checkpoint threshold differs by > 1%%")

    group = parser.add_argument_group("Output")
    group.add_argument("--out_dir", type=str, default=None, help="Output directory (None -> {work_dir}/calibration/<service>)")
    _add_bool(group, "--no_cache", False, "Ignore and overwrite the per-step score cache")
    _add_bool(group, "--write_checkpoint", False, "Save a calibrated copy {model_dir}/<service>_f2.pt (nll only)")

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
    if not 0 < args.p_grid_min <= args.p_grid_max <= 100 or args.p_grid_step <= 0:
        parser.error("--p_grid_*: need 0 < min <= max <= 100 and step > 0")
    if not 0 < args.prevalence < 1:
        parser.error("--prevalence must satisfy 0 < prevalence < 1")
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


def recording_step_scores(
    model: SyscallLSTM, checkpoint: dict, path: Path, step: int, device: torch.device, batch_size: int
) -> tuple[np.ndarray, np.ndarray] | None:
    """NLL (float32) і ранг справжнього виклику (int32) на кожному кроці для всіх вікон однієї записи,
    обидва [n_windows, seq_len], з одного проходу моделі; None, якщо вікон немає.

    Нарізка та сама, що в build_*_sequences: read_recording -> encode_recording -> make_sequences.
    """
    seq_len = checkpoint["seq_len"]
    lines = read_recording(str(path))
    if len(lines) < seq_len + 1:
        return None
    rows = encode_recording(checkpoint["vocabs"], lines, *checkpoint_features(checkpoint))
    X, y = make_sequences(rows, seq_len, step)
    if not len(X):
        return None
    nll_parts: list[np.ndarray] = []
    rank_parts: list[np.ndarray] = []
    with torch.no_grad():
        for x, y_batch in DataLoader(SequenceDataset(X, y), batch_size=batch_size, shuffle=False):
            y_batch = y_batch.to(device)
            logits = model(x.to(device))
            nll_parts.append(compute_step_scores(logits, y_batch).cpu().numpy().astype(np.float32))
            rank_parts.append(step_ranks(logits, y_batch[..., 0]).cpu().numpy())
    return np.concatenate(nll_parts, axis=0), np.concatenate(rank_parts, axis=0)


def compute_cache(
    model: SyscallLSTM, checkpoint: dict, args, val_files: list[Path], normal_files: list[Path],
    abnormal_files: list[Path], val_step: int, device: torch.device,
) -> dict[str, np.ndarray]:
    """Один прохід моделі по val і test: NLL і ранги на кроках, мітки вікон і індекс записи для кожного вікна."""
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


def plot_f2_heatmap(
    method: Method, fbeta_grid: np.ndarray, rows: list, p_grid: np.ndarray, selected, raw, beta: float, out_path: str
) -> None:
    fig, ax = plt.subplots(figsize=(11, 5 if len(rows) <= 12 else 8))
    im = ax.imshow(fbeta_grid, aspect="auto", origin="lower", cmap="viridis", interpolation="nearest")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label(f"F{beta:g} на калібрувальній частині")

    tick_idx = np.unique(np.linspace(0, len(p_grid) - 1, min(len(p_grid), 12)).round().astype(int))
    ax.set_xticks(tick_idx)
    ax.set_xticklabels([f"{p_grid[i]:.1f}" for i in tick_idx])
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(["середнє" if q == "mean" else f"{q:g}" for q in rows], fontsize=8 if len(rows) > 12 else None)

    point = f"({method.row_param}*, {method.col_param}*)"
    ax.scatter([raw[1]], [raw[0]], marker="x", s=90, color="#dc2626", linewidths=2, label="Сирий максимум")
    ax.scatter([selected[1]], [selected[0]], marker="*", s=220, color="white", edgecolors="black",
               linewidths=1, label=f"Обрана точка {point}")
    ax.set_xlabel(method.col_axis)
    ax.set_ylabel(method.row_axis)
    ax.set_title(method.title.format(f=f"F{beta:g}"))
    # легенда під графіком, щоб не закривати обрану точку
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, fontsize=8)
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


def plot_f2_comparison(summaries: list[dict], baseline: dict, beta: float, out_path: str) -> None:
    f = f"f{beta:g}"
    labels = [s["label"] for s in summaries]
    values = [s["holdout"][f] for s in summaries]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    x = np.arange(len(summaries))
    yerr = None
    if all(s["holdout"].get("ci95") for s in summaries):
        lo = [v - s["holdout"]["ci95"][f][0] for v, s in zip(values, summaries)]
        hi = [s["holdout"]["ci95"][f][1] - v for v, s in zip(values, summaries)]
        yerr = np.clip(np.array([lo, hi]), 0, None)
    ax.bar(x, values, yerr=yerr, capsize=6, color=[METHOD_COLORS[s["method"]] for s in summaries], alpha=0.85)
    ax.axhline(baseline["holdout"][f], color="black", linestyle="--", linewidth=1.2, label=BASELINE_LABEL)
    ax.set_xticks(x)
    ax.set_xticklabels([textwrap.fill(label, 18) for label in labels])
    ax.set_ylabel(f"F{beta:g} на відкладеній частині")
    ax.set_ylim(0, 1.02)
    ax.set_title("Порівняння методів оцінювання аномальності")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_pr_comparison(summaries: list[dict], curves: dict, is_attack: np.ndarray, out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    for s in summaries:
        color = METHOD_COLORS[s["method"]]
        precision, recall, _ = precision_recall_curve(is_attack, curves[s["method"]])
        ax.plot(recall, precision, color=color, label=s["label"])
        ax.scatter([s["holdout"]["recall"]], [s["holdout"]["precision"]], marker="*", s=200, color=color,
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


def plot_roc_comparison(summaries: list[dict], curves: dict, is_attack: np.ndarray, out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    for s in summaries:
        fpr, tpr, _ = roc_curve(is_attack, curves[s["method"]])
        ax.plot(fpr, tpr, color=METHOD_COLORS[s["method"]], label=f"{s['label']} (AUC = {s['holdout']['roc_auc']:.3f})")
    ax.plot([0, 1], [0, 1], color="gray", linestyle=":", linewidth=1)
    ax.set_xlabel("Частка хибних тривог (FPR)")
    ax.set_ylabel("Частка виявлених атак (TPR)")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.set_title("ROC-криві методів на відкладеній частині")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _fmt_ci(ci: dict | None, key: str) -> str:
    return "" if ci is None else f"[{ci[key][0]:.3f}, {ci[key][1]:.3f}]"


def log_comparison_table(result: dict, beta: float) -> None:
    """nll: базова лінія (чекпоінт) проти каліброваної точки."""
    f = f"f{beta:g}"
    base, sel = result["metrics"]["holdout"]["baseline"], result["metrics"]["holdout"]["selected"]
    bq, sq = result["baseline"], result["selected"]

    def agg_name(d: dict) -> str:
        return "mean" if d["window_agg"] == "mean" else f"q={d['q']:g}"

    rows = [
        ("window agg", agg_name(bq), agg_name(sq)),
        ("percentile p", f"{bq['p']:.1f}", f"{sq['p']:.1f}"),
        ("threshold", f"{bq['threshold']:.4f}", f"{sq['threshold']:.4f}"),
        ("TP / FP", f"{base['tp']} / {base['fp']}", f"{sel['tp']} / {sel['fp']}"),
        ("FN / TN", f"{base['fn']} / {base['tn']}", f"{sel['fn']} / {sel['tn']}"),
        ("precision", f"{base['precision']:.4f}", f"{sel['precision']:.4f}"),
        ("recall (TPR)", f"{base['recall']:.4f}", f"{sel['recall']:.4f}"),
        ("FPR", f"{base['fpr']:.4f}", f"{sel['fpr']:.4f}"),
        ("F1", f"{base['f1']:.4f}", f"{sel['f1']:.4f}"),
        (f"F{beta:g}", f"{base[f]:.4f}", f"{sel[f]:.4f}"),
        ("ROC-AUC", f"{base['roc_auc']:.4f}", f"{sel['roc_auc']:.4f}"),
    ]
    if "ci95" in sel:
        rows += [
            (f"F{beta:g} 95% CI", _fmt_ci(base["ci95"], f), _fmt_ci(sel["ci95"], f)),
            ("recall 95% CI", _fmt_ci(base["ci95"], "recall"), _fmt_ci(sel["ci95"], "recall")),
            ("FPR 95% CI", _fmt_ci(base["ci95"], "fpr"), _fmt_ci(sel["ci95"], "fpr")),
        ]
    logging.info(f"\n[nll] Holdout: baseline (checkpoint) vs calibrated, attack window share pi = {result['attack_fraction_holdout']:.4f}")
    logging.info(f"{'':<16}{'baseline':>20}{'calibrated':>20}")
    for name, b, s in rows:
        logging.info(f"{name:<16}{b:>20}{s:>20}")
    resc = result["prevalence_rescaled"]
    logging.info(
        f"RESCALED to prevalence={resc['prevalence']:g} (not measured, recomputed from TPR/FPR): "
        f"baseline precision={resc['baseline']['precision']:.4f} F{beta:g}={resc['baseline'][f]:.4f}; "
        f"calibrated precision={resc['selected']['precision']:.4f} F{beta:g}={resc['selected'][f]:.4f}"
    )


def log_methods_table(summaries: list[dict], baseline: dict, beta: float, prevalence: float) -> None:
    """Підсумкова таблиця всіх методів на holdout."""
    f = f"f{beta:g}"
    head = (f"{'method':<10}{'params':<24}{f'F{beta:g}':>8}{f'F{beta:g} 95% CI':>18}{'recall':>8}{'prec':>8}"
            f"{'FPR':>8}{'AUC':>8}{'dF2 vs nll':>12}{'dF2 95% CI':>20}{'sig':>5}{f'F{beta:g}@pi':>9}")
    logging.info(f"\nHoldout comparison (paired bootstrap on shared resamples; F{beta:g}@pi rescaled to prevalence={prevalence:g}):")
    logging.info(head)
    entries = [("baseline", f"{baseline['params']}", baseline["holdout"], None, baseline["prevalence_rescaled"])]
    entries += [(s["method"], s["params_text"], s["holdout"], s["delta_f2_vs_nll"], s["prevalence_rescaled"]) for s in summaries]
    for name, params, h, delta, resc in entries:
        ci = h.get("ci95")
        if delta is None:
            d, dci, sig = "", "", ""
        else:
            d = f"{delta['value']:+.4f}"
            dci = "" if delta["ci95"] is None else f"[{delta['ci95'][0]:+.3f}, {delta['ci95'][1]:+.3f}]"
            sig = "" if delta["ci95"] is None else ("yes" if delta["significant"] else "no")
        logging.info(
            f"{name:<10}{params:<24}{h[f]:>8.4f}{_fmt_ci(ci, f):>18}{h['recall']:>8.4f}{h['precision']:>8.4f}"
            f"{h['fpr']:>8.4f}{h['roc_auc']:>8.4f}{d:>12}{dci:>20}{sig:>5}{resc[f]:>9.4f}"
        )


def write_grid_csv(
    path: str, method: Method, grid: dict, rows: list, p_grid: np.ndarray, smoothed: np.ndarray, beta: float
) -> None:
    """nll: формат без змін; topk: + k_eff; run_*: m, p, tau (+ k_eff для рангів)."""
    f = f"f{beta:g}"
    metric_cols = ["tp", "fp", "fn", "tn", "precision", "recall", "fpr", "f1", f]
    with_k = method.step_key == "rank"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if method.family == "quantile":
            head = ["window_agg", "q", "p", "threshold"]
        else:
            head = ["m", "p", "tau"]
        writer.writerow([*head, *(["k_eff"] if with_k else []), *metric_cols, f"{f}_smoothed"])
        for i, row in enumerate(rows):
            if method.family == "quantile":
                label = _row_label(row)
                key = [label["window_agg"], "" if label["q"] is None else f"{label['q']:g}"]
            else:
                key = [int(row)]
            for j, p in enumerate(p_grid):
                thr = grid["threshold"][i, j].item()
                writer.writerow([
                    *key, f"{p:.1f}", thr, *([math.floor(thr)] if with_k else []),
                    *[grid[c][i, j].item() for c in metric_cols], smoothed[i, j].item(),
                ])


def _point(method: Method, rows: list, p_grid: np.ndarray, grid: dict, ij: tuple[int, int], f: str) -> dict:
    """Опис точки сітки для calibration.json: параметри, поріг (θ або τ), k_eff для рангів, F-метрика на calib."""
    i, j = ij
    thr = float(grid["threshold"][i, j])
    out = {**_param_label(method, rows[i]), "p": float(p_grid[j])}
    out["threshold" if method.family == "quantile" else "tau"] = thr
    if method.step_key == "rank":
        out["k_eff"] = math.floor(thr)
    if method.family == "run":
        out["rule"] = "R >= m"
    out[f] = float(grid["fbeta"][i, j])
    return out


def evaluate_holdout(
    scores: np.ndarray, threshold: float, ctx: dict, beta: float
) -> tuple[dict, dict[str, np.ndarray] | None]:
    """Метрики holdout (+ ROC-AUC) і, якщо бутстреп увімкнено, метрики на спільних ресемплах та 95% ДІ."""
    mask, is_attack = ctx["holdout_mask"], ctx["test_is_attack"]
    m = point_metrics(scores[mask], is_attack[mask], threshold, beta)
    m["roc_auc"] = float(roc_auc_score(is_attack[mask], scores[mask]))
    boot = None
    if ctx["sample"] is not None:
        boot = bootstrap_metrics(scores, is_attack, ctx["test_rec_idx"], ctx["holdout_order"], threshold, ctx["sample"], beta)
        m["ci95"] = ci95_summary(boot, beta)
    return m, boot


def _rescaled(m: dict, prevalence: float, beta: float) -> dict:
    precision = float(precision_at_prevalence(m["recall"], m["fpr"], prevalence))
    return {"precision": precision, "recall": m["recall"], f"f{beta:g}": float(fbeta(precision, m["recall"], beta))}


def calibrate_method(method: Method, rows: list, p_grid: np.ndarray, ctx: dict, common: dict, args) -> dict:
    """Сітка на calib, вибір точки (згладжування 3×3), метрики calib/holdout, файли у {out_dir}/{метод}/."""
    beta = args.beta
    f = f"f{beta:g}"
    val_steps, test_steps = ctx["steps"][method.step_key]
    calib_mask, holdout_mask, test_is_attack = ctx["calib_mask"], ctx["holdout_mask"], ctx["test_is_attack"]
    is_ref = method.name == REFERENCE_METHOD

    grid = method.search(val_steps, test_steps[calib_mask], test_is_attack[calib_mask], rows, p_grid, beta)
    mean_row = rows.index("mean") if "mean" in rows else None
    (si, sj), (ri, rj), smoothed = smooth_select(grid["fbeta"], mean_row)
    on_edge = edge_flags((si, sj), grid["fbeta"].shape, mean_row)
    if on_edge["row"] or on_edge["col"]:
        axes = " and ".join(name for name, flag in ((method.row_param, on_edge["row"]), ("p", on_edge["col"])) if flag)
        logging.warning(f"WARNING: [{method.name}] selected point is on the grid edge ({axes}): consider widening the grid")

    sel_row, sel_p = rows[si], float(p_grid[sj])
    scores, sel_threshold = method.operating_point(val_steps, test_steps, sel_row, sel_p)

    named = [("selected", scores, sel_threshold)]
    if is_ref:
        named.append(("baseline", ctx["baseline_scores"], ctx["baseline_threshold"]))
    metrics: dict = {"calib": {}, "holdout": {}}
    boots: dict = {}
    for name, sc, thr in named:
        metrics["calib"][name] = point_metrics(sc[calib_mask], test_is_attack[calib_mask], thr, beta)
    for name, sc, thr in named:
        metrics["holdout"][name], boots[name] = evaluate_holdout(sc, thr, ctx, beta)

    rescaled = {"prevalence": args.prevalence}
    for name, _, _ in named:
        rescaled[name] = _rescaled(metrics["holdout"][name], args.prevalence, beta)

    selected = {**_point(method, rows, p_grid, grid, (si, sj), f), f"{f}_smoothed": float(smoothed[si, sj]), "on_edge": on_edge}
    grid_desc = {
        "p": {"min": args.p_grid_min, "max": args.p_grid_max, "step": args.p_grid_step}, "beta": beta,
    }
    if method.family == "quantile":
        grid_desc = {"q": [float(q) for q in args.q_grid], "include_mean": bool(args.include_mean), **grid_desc,
                     "smoothing": "3x3 mean (edges: available neighbours); mean row along p only"}
    else:
        grid_desc = {"m": [int(m) for m in rows], **grid_desc, "p_kind": "percentile of all val step scores",
                     "smoothing": "3x3 mean (edges: available neighbours)"}

    result = {
        "method": method.name,
        "label": method.label,
        "row_param": method.row_param,
        "col_param": method.col_param,
        "step_score": method.step_key,
        **common,
        "grid": grid_desc,
        "selected": selected,
        "raw_max": _point(method, rows, p_grid, grid, (ri, rj), f),
        "baseline": ctx["baseline_desc"] if is_ref else None,
        "metrics": metrics,
        "attack_fraction_holdout": ctx["attack_fraction_holdout"],
        "prevalence_rescaled": rescaled,
    }
    if is_ref:
        result["sanity"] = ctx["sanity"]

    method_dir = os.path.join(ctx["out_dir"], method.name)
    os.makedirs(method_dir, exist_ok=True)
    with open(os.path.join(method_dir, "calibration.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
    write_grid_csv(os.path.join(method_dir, "grid.csv"), method, grid, rows, p_grid, smoothed, beta)
    plot_f2_heatmap(method, grid["fbeta"], rows, p_grid, (si, sj), (ri, rj), beta, os.path.join(method_dir, "f2_heatmap.png"))
    plot_pr_curve(
        method, test_is_attack[holdout_mask], scores[holdout_mask], metrics["holdout"]["selected"],
        metrics["holdout"].get("baseline"), os.path.join(method_dir, "pr_curve_holdout.png"),
    )
    if is_ref:
        log_comparison_table(result, beta)
    raw = result["raw_max"]
    logging.info(
        f"[{method.name}] selected: {_param_text(method, sel_row)} p={sel_p:.1f} "
        f"{'threshold' if method.family == 'quantile' else 'tau'}={grid['threshold'][si, sj]:.4f}"
        f"{' k_eff=' + str(selected['k_eff']) if 'k_eff' in selected else ''}; "
        f"raw max: {_param_text(method, rows[ri])} p={raw['p']:.1f} F{beta:g}={raw[f]:.4f}"
    )

    summary_selected = {k: v for k, v in selected.items() if k not in (f, f"{f}_smoothed")}
    return {
        "method": method.name,
        "label": method.label,
        "step_score": method.step_key,
        "row_param": method.row_param,
        "col_param": method.col_param,
        "params_text": f"{_param_text(method, sel_row)} p={sel_p:.1f}",
        "selected": summary_selected,
        "calib": {f: float(grid["fbeta"][si, sj]), f"{f}_smoothed": float(smoothed[si, sj])},
        "holdout": metrics["holdout"]["selected"],
        "prevalence_rescaled": rescaled["selected"],
        "calibration_json": f"{method.name}/calibration.json",
        "_boot": boots["selected"],
        "_scores": scores[holdout_mask],
        "_result": result,
    }


def write_comparison(summaries: list[dict], baseline: dict, common: dict, ctx: dict, args) -> None:
    beta = args.beta
    f = f"f{beta:g}"
    out = os.path.join(ctx["out_dir"], "comparison")
    os.makedirs(out, exist_ok=True)

    ref = next((s for s in summaries if s["method"] == REFERENCE_METHOD), None)
    if ref is None:
        logging.info(f"{REFERENCE_METHOD} is not in --methods: paired dF2 vs {REFERENCE_METHOD} is not computed")
    for s in summaries:
        if ref is None:
            s["delta_f2_vs_nll"] = None
            continue
        delta = {"value": s["holdout"][f] - ref["holdout"][f], "ci95": None, "significant": None}
        if s["_boot"] is not None:
            delta.update(paired_delta_ci(s["_boot"][f], ref["_boot"][f]))
        s["delta_f2_vs_nll"] = delta

    comparison = {
        **{k: common[k] for k in ("service", "checkpoint", "git_commit", "data_fingerprint", "split_seed",
                                  "calib_fraction", "windows")},
        "beta": beta,
        "prevalence": args.prevalence,
        "split": {part: {k: v for k, v in common["split"][part].items() if k.startswith("n_")}
                  for part in ("calib", "holdout")},
        "attack_fraction_holdout": ctx["attack_fraction_holdout"],
        "bootstrap": {"n": args.bootstrap, "seed": args.split_seed, "unit": "recording", "stratified": True,
                      "shared_resamples": True} if args.bootstrap else None,
        "reference_method": REFERENCE_METHOD if ref is not None else None,
        "baseline": {k: v for k, v in baseline.items() if k != "params"},
        "methods": [{k: v for k, v in s.items() if not k.startswith("_") and k != "params_text"} for s in summaries],
    }
    with open(os.path.join(out, "comparison.json"), "w", encoding="utf-8") as fh:
        json.dump(comparison, fh, indent=2, ensure_ascii=False)

    def ci_cells(h: dict, key: str) -> list:
        ci = h.get("ci95")
        return ["", ""] if ci is None else ci[key]

    with open(os.path.join(out, "comparison.csv"), "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "method", "label", "row_param", "row_value", "p", "threshold", "tau", "k_eff",
            f, f"{f}_lo", f"{f}_hi", "recall", "recall_lo", "recall_hi", "precision", "fpr", "fpr_lo", "fpr_hi",
            "roc_auc", f"delta_{f}", f"delta_{f}_lo", f"delta_{f}_hi", "significant",
            "precision_at_prev", f"{f}_at_prev",
        ])
        b = baseline
        writer.writerow([
            "baseline", b["label"], "q", "mean" if b["window_agg"] == "mean" else b["q"], b["p"], b["threshold"], "", "",
            b["holdout"][f], *ci_cells(b["holdout"], f), b["holdout"]["recall"], *ci_cells(b["holdout"], "recall"),
            b["holdout"]["precision"], b["holdout"]["fpr"], *ci_cells(b["holdout"], "fpr"), b["holdout"]["roc_auc"],
            "", "", "", "", b["prevalence_rescaled"]["precision"], b["prevalence_rescaled"][f],
        ])
        for s in summaries:
            sel, h, d = s["selected"], s["holdout"], s["delta_f2_vs_nll"]
            row_value = sel.get("m", sel.get("q")) if sel.get("window_agg") != "mean" else "mean"
            d_cells = ["", "", "", ""] if d is None else [
                d["value"], *(d["ci95"] if d["ci95"] is not None else ["", ""]),
                "" if d["significant"] is None else d["significant"],
            ]
            writer.writerow([
                s["method"], s["label"], s["row_param"], row_value, sel["p"], sel.get("threshold", ""),
                sel.get("tau", ""), sel.get("k_eff", ""),
                h[f], *ci_cells(h, f), h["recall"], *ci_cells(h, "recall"), h["precision"], h["fpr"],
                *ci_cells(h, "fpr"), h["roc_auc"], *d_cells,
                s["prevalence_rescaled"]["precision"], s["prevalence_rescaled"][f],
            ])

    is_attack = ctx["test_is_attack"][ctx["holdout_mask"]]
    curves = {s["method"]: s["_scores"] for s in summaries}
    plot_f2_comparison(summaries, baseline, beta, os.path.join(out, "f2_comparison.png"))
    plot_pr_comparison(summaries, curves, is_attack, os.path.join(out, "pr_comparison.png"))
    plot_roc_comparison(summaries, curves, is_attack, os.path.join(out, "roc_comparison.png"))
    log_methods_table(summaries, baseline, beta, args.prevalence)
    logging.info(f"Comparison: {out}")


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
    f = f"f{beta:g}"

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

    # один поділ і одні бутстреп-ресемпли для всіх методів
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
            f"bootstrap intervals and dF2 significance are unreliable (< {MIN_BOOTSTRAP_RECORDINGS} per class)"
        )

    p_grid = np.round(np.arange(args.p_grid_min, args.p_grid_max + args.p_grid_step / 2, args.p_grid_step), 6)
    q_rows: list = list(args.q_grid) + (["mean"] if args.include_mean else [])
    m_rows = [m for m in args.m_grid if m <= seq_len]
    if len(m_rows) < len(args.m_grid):
        logging.info(f"--m_grid: values > seq_len={seq_len} dropped (a window has only {seq_len} steps)")
    methods = build_methods(args.methods)
    if any(m.family == "run" for m in methods) and not m_rows:
        parser.error(f"--m_grid has no values <= seq_len={seq_len}")

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
        "calib_mask": calib_mask,
        "holdout_mask": holdout_mask,
        "holdout_order": np.concatenate([holdout_normal, holdout_abnormal]),
        "sample": sample,
        "attack_fraction_holdout": float(test_is_attack[holdout_mask].mean()),
        "sanity": sanity,
        "baseline_scores": aggregate(test_nll, base_q),
        "baseline_threshold": float(checkpoint["threshold"]),
        "baseline_desc": {**_row_label(base_q), "p": baseline_p,
                          "p_source": "train_args" if "threshold_percentile" in train_args else "--baseline_p",
                          "threshold": float(checkpoint["threshold"]), "checkpoint_window_agg": checkpoint["window_agg"]},
    }

    # базова лінія (чекпоінт, NLL) потрібна для порівняння незалежно від --methods
    base_holdout, _ = evaluate_holdout(ctx["baseline_scores"], ctx["baseline_threshold"], ctx, beta)
    baseline = {
        "label": BASELINE_LABEL, **_row_label(base_q), "p": baseline_p, "threshold": ctx["baseline_threshold"],
        "holdout": base_holdout, "prevalence_rescaled": _rescaled(base_holdout, args.prevalence, beta),
        "params": f"{'mean' if base_q == 'mean' else f'q={base_q:g}'} p={baseline_p:.1f}",
    }

    summaries = [
        calibrate_method(m, q_rows if m.family == "quantile" else m_rows, p_grid, ctx, common, args) for m in methods
    ]
    write_comparison(summaries, baseline, common, ctx, args)
    logging.info(f"Results: {out_dir}")

    if args.write_checkpoint:
        if len(methods) > 1:
            logging.info("--write_checkpoint: only nll is written to the checkpoint (inference supports only nll); "
                         "parameters of the other methods stay in their calibration.json")
        nll_result = next(s["_result"] for s in summaries if s["method"] == REFERENCE_METHOD)
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
