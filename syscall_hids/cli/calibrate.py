"""Калібрування квантиля агрегації вікна q і перцентиля порогу p під F2 (calib/holdout за записами).

Usage:
    hids-calibrate --service PHP_CWE-434
    hids-calibrate --config configs/php_cwe_434.yaml --service PHP_CWE-434 --write_checkpoint
    hids-calibrate --service FIXT --checkpoint tests/golden/FIXT.pt --dataset_root tests/golden/data --val_step 32
"""

import csv
import hashlib
import json
import logging
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from sklearn.metrics import precision_recall_curve, roc_auc_score
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
    aggregate,
    bootstrap_ci,
    confusion_at_threshold,
    fbeta,
    grid_search,
    metrics_from_confusion,
    precision_at_prevalence,
    smooth_select,
    split_recordings,
)
from syscall_hids.tools.checkpoint import checkpoint_features, load_model
from syscall_hids.tools.utils import get_git_commit

Q_GRID_DEFAULT = [0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.99, 1.0]
SANITY_REL_TOL = 1e-4  # відносна розбіжність порогу, вище якої — попередження
SANITY_REL_FAIL = 0.01  # вище — зупинка (якщо не --ignore_sanity)
CACHE_VERSION = 1


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
    group.add_argument("--calib_fraction", type=float, default=0.5, help="Share of test recordings in the calib part")
    # окреме ім'я замість --seed: seed зі збережених конфігів навчання не впливає на поділ
    group.add_argument("--split_seed", type=int, default=0, help="Seed for the calib/holdout split and the bootstrap")
    group.add_argument("--q_grid", type=float, nargs="+", default=Q_GRID_DEFAULT, help="Window aggregation quantiles")
    _add_bool(group, "--include_mean", True, "Add window_agg=mean as a separate grid row")
    group.add_argument("--p_grid_min", type=float, default=90.0, help="Smallest threshold percentile")
    group.add_argument("--p_grid_max", type=float, default=99.9, help="Largest threshold percentile")
    group.add_argument("--p_grid_step", type=float, default=0.1, help="Threshold percentile step")
    group.add_argument("--beta", type=float, default=2.0, help="beta of F-beta")
    group.add_argument("--prevalence", type=float, default=0.01, help="Realistic attack share for the precision rescale")
    group.add_argument("--bootstrap", type=int, default=1000, help="Bootstrap resamples on holdout (0: off)")
    _add_bool(group, "--ignore_sanity", False, "Continue even if the recomputed checkpoint threshold differs by > 1%%")

    group = parser.add_argument_group("Output")
    group.add_argument("--out_dir", type=str, default=None, help="Output directory (None -> {work_dir}/calibration/<service>)")
    _add_bool(group, "--no_cache", False, "Ignore and overwrite the per-step NLL cache")
    _add_bool(group, "--write_checkpoint", False, "Save a calibrated copy {model_dir}/<service>_f2.pt")

    _add_dir_args(parser, model_dir=True)
    _add_ram_args(parser)
    return parser


def _check_calibrate_args(parser, args) -> None:
    if not all(0 < q <= 1 for q in args.q_grid):
        parser.error("--q_grid: every value must satisfy 0 < q <= 1")
    if not 0 < args.calib_fraction < 1:
        parser.error("--calib_fraction must satisfy 0 < calib_fraction < 1")
    if not 0 < args.p_grid_min <= args.p_grid_max <= 100 or args.p_grid_step <= 0:
        parser.error("--p_grid_*: need 0 < min <= max <= 100 and step > 0")
    if not 0 < args.prevalence < 1:
        parser.error("--prevalence must satisfy 0 < prevalence < 1")
    if args.bootstrap < 0:
        parser.error("--bootstrap must be >= 0")


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


def recording_step_nll(
    model: SyscallLSTM, checkpoint: dict, path: Path, step: int, device: torch.device, batch_size: int
) -> np.ndarray | None:
    """NLL на кожному кроці для всіх вікон однієї записи [n_windows, seq_len] (float32) або None, якщо вікон немає.

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
    parts: list[np.ndarray] = []
    with torch.no_grad():
        for x, y_batch in DataLoader(SequenceDataset(X, y), batch_size=batch_size, shuffle=False):
            step_scores = compute_step_scores(model(x.to(device)), y_batch.to(device))
            parts.append(step_scores.cpu().numpy().astype(np.float32))
    return np.concatenate(parts, axis=0)


def compute_cache(
    model: SyscallLSTM, checkpoint: dict, args, val_files: list[Path], normal_files: list[Path],
    abnormal_files: list[Path], val_step: int, device: torch.device,
) -> dict[str, np.ndarray]:
    """Один прохід моделі по val і test: NLL на кроках, мітки вікон і індекс записи для кожного вікна."""
    seq_len = checkpoint["seq_len"]
    every = args.ram_check_every_n_recordings

    val_parts: list[np.ndarray] = []
    for i, path in enumerate(val_files):
        nll = recording_step_nll(model, checkpoint, path, val_step, device, args.batch_size)
        if nll is not None:
            val_parts.append(nll)
        if (i + 1) % every == 0:
            resource_guard.check_ram(f"{args.service}/val: after {i + 1} recordings")

    test_parts: list[np.ndarray] = []
    rec_idx_parts: list[np.ndarray] = []
    rec_files: list[str] = []
    rec_is_attack: list[bool] = []
    for group, files in ((False, normal_files), (True, abnormal_files)):
        for i, path in enumerate(files):
            nll = recording_step_nll(model, checkpoint, path, seq_len, device, args.batch_size)
            if nll is not None:
                rec_idx_parts.append(np.full(len(nll), len(rec_files), dtype=np.int32))
                test_parts.append(nll)
                rec_files.append(path.relative_to(args.dataset_root).as_posix())
                rec_is_attack.append(group)
            if (i + 1) % every == 0:
                resource_guard.check_ram(f"{args.service}/test: after {i + 1} recordings")

    if not val_parts or not test_parts:
        raise ValueError(f"[{args.service}] val or test split has no windows of length {seq_len + 1}")

    rec_is_attack_arr = np.array(rec_is_attack, dtype=bool)
    rec_idx = np.concatenate(rec_idx_parts)
    return {
        "val_nll": np.concatenate(val_parts),
        "test_nll": np.concatenate(test_parts),
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


def plot_f2_heatmap(fbeta_grid: np.ndarray, rows: list, p_grid: np.ndarray, selected, raw, beta: float, out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(11, 5))
    im = ax.imshow(fbeta_grid, aspect="auto", origin="lower", cmap="viridis", interpolation="nearest")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label(f"F{beta:g} на калібрувальній частині")

    tick_idx = np.unique(np.linspace(0, len(p_grid) - 1, min(len(p_grid), 12)).round().astype(int))
    ax.set_xticks(tick_idx)
    ax.set_xticklabels([f"{p_grid[i]:.1f}" for i in tick_idx])
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(["середнє" if q == "mean" else f"{q:g}" for q in rows])

    ax.scatter([raw[1]], [raw[0]], marker="x", s=90, color="#dc2626", linewidths=2, label="Сирий максимум")
    ax.scatter([selected[1]], [selected[0]], marker="*", s=220, color="white", edgecolors="black",
               linewidths=1, label="Обрана точка (q*, p*)")
    ax.set_xlabel("Перцентиль порогу на валідаційній вибірці, p")
    ax.set_ylabel("Квантиль агрегації вікна, q")
    ax.set_title(f"Залежність F{beta:g} від параметрів агрегації та порогу")
    ax.legend(loc="lower left", fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_pr_curve(is_attack: np.ndarray, scores: np.ndarray, selected: dict, baseline: dict, out_path: str) -> None:
    precision, recall, _ = precision_recall_curve(is_attack, scores)
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.plot(recall, precision, color="#2563eb", label="Крива для q*")
    ax.scatter([selected["recall"]], [selected["precision"]], marker="*", s=200, color="#dc2626",
               edgecolors="black", zorder=3, label="Робоча точка (q*, p*)")
    ax.scatter([baseline["recall"]], [baseline["precision"]], marker="o", s=60, color="#16a34a",
               edgecolors="black", zorder=3, label="Базова лінія (чекпоінт)")
    ax.set_xlabel("Повнота (recall)")
    ax.set_ylabel("Точність (precision)")
    ax.set_xlim(0, 1.02)
    ax.set_ylim(0, 1.02)
    ax.set_title("Крива точність–повнота на відкладеній частині")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _fmt_ci(ci: dict | None, key: str) -> str:
    return "" if ci is None else f"[{ci[key][0]:.3f}, {ci[key][1]:.3f}]"


def log_comparison_table(result: dict, beta: float) -> None:
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
    logging.info(f"\nHoldout: baseline (checkpoint) vs calibrated, attack window share pi = {result['attack_fraction_holdout']:.4f}")
    logging.info(f"{'':<16}{'baseline':>20}{'calibrated':>20}")
    for name, b, s in rows:
        logging.info(f"{name:<16}{b:>20}{s:>20}")
    resc = result["prevalence_rescaled"]
    logging.info(
        f"RESCALED to prevalence={resc['prevalence']:g} (not measured, recomputed from TPR/FPR): "
        f"baseline precision={resc['baseline']['precision']:.4f} F{beta:g}={resc['baseline'][f]:.4f}; "
        f"calibrated precision={resc['selected']['precision']:.4f} F{beta:g}={resc['selected'][f]:.4f}"
    )


def write_grid_csv(path: str, grid: dict, rows: list, p_grid: np.ndarray, smoothed: np.ndarray, beta: float) -> None:
    f = f"f{beta:g}"
    columns = ["threshold", "tp", "fp", "fn", "tn", "precision", "recall", "fpr", "f1", f]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["window_agg", "q", "p", *columns, f"{f}_smoothed"])
        for i, q in enumerate(rows):
            label = _row_label(q)
            for j, p in enumerate(p_grid):
                writer.writerow([
                    label["window_agg"], "" if label["q"] is None else f"{label['q']:g}", f"{p:.1f}",
                    *[grid[c][i, j].item() for c in columns], smoothed[i, j].item(),
                ])


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
    logging.info(f"Per-step NLL {'loaded from cache' if from_cache else 'computed and cached'}: {cache_path}")
    val_nll, test_nll = cache["val_nll"], cache["test_nll"]
    test_is_attack, test_rec_idx = cache["test_is_attack"], cache["test_rec_idx"]
    test_files, rec_is_attack = cache["test_files"], cache["test_rec_is_attack"]
    logging.info(
        f"val windows: {len(val_nll)} (step {val_step}), test windows: {len(test_nll)} "
        f"({int(test_is_attack.sum())} attack) from {len(test_files)} recordings"
    )

    sanity = sanity_check(val_nll, checkpoint, baseline_p, args.ignore_sanity)

    calib_recs, holdout_recs = split_recordings(rec_is_attack, args.calib_fraction, args.split_seed)
    calib_mask = np.isin(test_rec_idx, calib_recs)
    holdout_mask = ~calib_mask
    if test_is_attack[holdout_mask].all() or not test_is_attack[holdout_mask].any():
        raise SystemExit("holdout has only one window class: need at least 2 normal and 2 abnormal recordings")

    rows: list = list(args.q_grid) + (["mean"] if args.include_mean else [])
    p_grid = np.round(np.arange(args.p_grid_min, args.p_grid_max + args.p_grid_step / 2, args.p_grid_step), 6)
    grid = grid_search(val_nll, test_nll[calib_mask], test_is_attack[calib_mask], rows, p_grid, beta)
    mean_row = len(rows) - 1 if args.include_mean else None
    (si, sj), (ri, rj), smoothed = smooth_select(grid["fbeta"], mean_row)

    sel_q, base_q = rows[si], _checkpoint_agg(checkpoint)
    sel_threshold = float(grid["threshold"][si, sj])
    base_threshold = float(checkpoint["threshold"])

    metrics: dict = {"calib": {}, "holdout": {}}
    for part, mask in (("calib", calib_mask), ("holdout", holdout_mask)):
        for name, q, thr in (("selected", sel_q, sel_threshold), ("baseline", base_q, base_threshold)):
            scores = aggregate(test_nll[mask], q)
            metrics[part][name] = point_metrics(scores, test_is_attack[mask], thr, beta)
            if part == "holdout":
                metrics[part][name]["roc_auc"] = float(roc_auc_score(test_is_attack[mask], scores))
                if args.bootstrap:
                    metrics[part][name]["ci95"] = bootstrap_ci(
                        aggregate(test_nll, q), test_is_attack, test_rec_idx,
                        holdout_recs[~rec_is_attack[holdout_recs]], holdout_recs[rec_is_attack[holdout_recs]],
                        thr, args.bootstrap, args.split_seed, beta,
                    )

    rescaled = {"prevalence": args.prevalence}
    for name in ("selected", "baseline"):
        m = metrics["holdout"][name]
        precision = float(precision_at_prevalence(m["recall"], m["fpr"], args.prevalence))
        rescaled[name] = {"precision": precision, "recall": m["recall"], f: float(fbeta(precision, m["recall"], beta))}

    def files_of(recs: np.ndarray) -> dict:
        part_mask = np.isin(test_rec_idx, recs)
        return {
            "normal": [str(test_files[r]) for r in recs if not rec_is_attack[r]],
            "abnormal": [str(test_files[r]) for r in recs if rec_is_attack[r]],
            "n_windows": int(part_mask.sum()),
            "n_attack_windows": int(test_is_attack[part_mask].sum()),
        }

    result = {
        "service": args.service,
        "checkpoint": {"path": str(checkpoint_path), "sha256": checkpoint_sha256},
        "git_commit": get_git_commit(),
        "split_seed": args.split_seed,
        "calib_fraction": args.calib_fraction,
        "dataset_root": str(args.dataset_root),
        "data_fingerprint": fingerprint,
        "windows": {"seq_len": int(seq_len), "test_step": int(seq_len), "val_step": int(val_step), "n_val_windows": int(len(val_nll))},
        "split": {"calib": files_of(calib_recs), "holdout": files_of(holdout_recs)},
        "grid": {
            "q": [float(q) for q in args.q_grid], "include_mean": bool(args.include_mean),
            "p": {"min": args.p_grid_min, "max": args.p_grid_max, "step": args.p_grid_step}, "beta": beta,
            "smoothing": "3x3 mean (edges: available neighbours); mean row along p only",
        },
        "selected": {**_row_label(sel_q), "p": float(p_grid[sj]), "threshold": sel_threshold,
                     f"{f}_smoothed": float(smoothed[si, sj]), f: float(grid["fbeta"][si, sj])},
        "raw_max": {**_row_label(rows[ri]), "p": float(p_grid[rj]), "threshold": float(grid["threshold"][ri, rj]),
                    f: float(grid["fbeta"][ri, rj])},
        "baseline": {**_row_label(base_q), "p": baseline_p,
                     "p_source": "train_args" if "threshold_percentile" in train_args else "--baseline_p",
                     "threshold": base_threshold, "checkpoint_window_agg": checkpoint["window_agg"]},
        "sanity": sanity,
        "metrics": metrics,
        "attack_fraction_holdout": float(test_is_attack[holdout_mask].mean()),
        "prevalence_rescaled": rescaled,
    }

    json_path = os.path.join(out_dir, "calibration.json")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
    write_grid_csv(os.path.join(out_dir, "grid.csv"), grid, rows, p_grid, smoothed, beta)
    plot_f2_heatmap(grid["fbeta"], rows, p_grid, (si, sj), (ri, rj), beta, os.path.join(out_dir, "f2_heatmap.png"))
    plot_pr_curve(
        test_is_attack[holdout_mask], aggregate(test_nll[holdout_mask], sel_q),
        metrics["holdout"]["selected"], metrics["holdout"]["baseline"], os.path.join(out_dir, "pr_curve_holdout.png"),
    )

    log_comparison_table(result, beta)
    logging.info(
        f"\nSelected: {result['selected']['window_agg']} q={result['selected']['q']} p={result['selected']['p']:.1f} "
        f"threshold={sel_threshold:.4f}; raw max: q={result['raw_max']['q']} p={result['raw_max']['p']:.1f} "
        f"F{beta:g}={result['raw_max'][f]:.4f}"
    )
    logging.info(f"Results: {out_dir}")

    if args.write_checkpoint:
        out_ckpt = Path(args.model_dir) / f"{args.service}_f2.pt"
        if out_ckpt.resolve() == checkpoint_path.resolve():
            raise SystemExit(f"Refusing to overwrite the source checkpoint {checkpoint_path}")
        calibrated = dict(checkpoint)
        calibrated["window_agg"] = "mean" if sel_q == "mean" else "quantile"
        if sel_q != "mean":
            calibrated["window_agg_quantile"] = float(sel_q)
        calibrated["threshold"] = sel_threshold
        calibrated["calibration"] = result
        os.makedirs(out_ckpt.parent, exist_ok=True)
        torch.save(calibrated, out_ckpt)
        logging.info(f"Calibrated checkpoint copy: {out_ckpt}")


if __name__ == "__main__":
    main()
