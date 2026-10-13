"""Порівняння методів оцінювання аномальності за критерієм Неймана-Пірсона (hids-np).

Рівень хибних тривог α задається заздалегідь (--alphas) і не підбирається за розміченими атаками.
Для кожного методу й кожного α:
- поріг τ — найменше значення статистики вікна s(w) серед нормальних вікон val, для якого частка вікон val
  з s > τ не перевищує α (без інтерполяції; досягнутий α' <= α виводиться поруч);
- гіперпараметр статистики (q для nll і topk, кроковий перцентиль p для run_nll і run_rank) обирається
  на calib-частині test за максимумом recall, причому τ для кожного кандидата перераховується за val під той
  самий α; за рівного recall — менший α', далі перший у сітці;
- метрики на holdout: recall, precision, F1, FPR вікон, ROC-AUC статистики і FPR на рівні записів
  (частка нормальних записів хоча б з однією тривогою). F1 лише метрика, у виборі не бере участі.

Для topk поріг τ над квантилем рангів задає ефективне k = ⌊τ⌋; для серійних методів τ над довжиною
серії R задає мінімальну довжину m = ⌊τ⌋ + 1 (вікно аномальне, якщо R > τ).

Кеш NLL і рангів і поділ calib/holdout — ті самі, що в hids-calibrate: за однакових --split_seed і
--calib_fraction частини збігаються, а --cache може вказувати на готовий кеш hids-calibrate.

Usage:
    hids-np --config configs/php_cwe_434.yaml --service PHP_CWE-434
    hids-np --service PHP_CWE-434 --cache runs/x/calibration/PHP_CWE-434/cache_PHP_CWE-434.npz
"""

import csv
import json
import logging
import os
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import roc_auc_score

from syscall_hids.cli.calibrate import (
    CACHE_VERSION,
    Q_GRID_DEFAULT,
    compute_cache,
    data_fingerprint,
    load_or_compute_cache,
    sha256_file,
)
from syscall_hids.data.layout import recording_files, test_recording_files
from syscall_hids.tools import resource_guard
from syscall_hids.tools.arg_parser import _add_bool, _add_dir_args, _add_ram_args, _new_parser
from syscall_hids.tools.arg_parser_tools import check_args
from syscall_hids.tools.calibration import (
    METHOD_NAMES,
    aggregate,
    build_methods,
    default_p_grid,
    max_run_length,
    metrics_from_confusion,
    record_flags,
    record_metrics,
    split_recordings,
)
from syscall_hids.tools.checkpoint import load_model
from syscall_hids.tools.utils import get_git_commit

ALPHAS_DEFAULT = [0.001, 0.01, 0.05]


def build_np_arg_parser(description: str | None = None):
    """Парсер hids-np. Невідомі ключі YAML ігноруються: можна передати конфіг навчання."""
    parser = _new_parser(ignore_unknown_config_file_keys=True, description=description)
    group = parser.add_argument_group("Data and model")
    group.add_argument("--service", required=True, help="Scenario name (dataset subdirectory)")
    group.add_argument("--checkpoint", default=None, help="Path to the .pt (default: {model_dir}/<service>.pt)")
    group.add_argument("--dataset_root", type=str, default="./DATASET_LIDDS", help="Dataset root")
    group.add_argument("--val_step", type=int, default=None,
                       help="Validation window step (default: train_args.seq_step from the checkpoint)")
    group.add_argument("--batch_size", type=int, default=32, help="Inference batch size")
    group.add_argument("--device", type=str, default=None, help="torch device (default: cuda if available, else cpu)")

    group = parser.add_argument_group("Neyman-Pearson")
    group.add_argument("--methods", nargs="+", choices=METHOD_NAMES, default=list(METHOD_NAMES),
                       help="Scoring methods to compare")
    group.add_argument("--alphas", type=float, nargs="+", default=ALPHAS_DEFAULT,
                       help="Window false alarm levels alpha on val, fixed in advance")
    group.add_argument("--auc_alpha", type=float, default=0.01,
                       help="ROC-AUC in the summary table is given for the statistic selected at this alpha")
    group.add_argument("--q_grid", type=float, nargs="+", default=Q_GRID_DEFAULT,
                       help="Window aggregation quantiles (nll, topk)")
    _add_bool(group, "--include_mean", True, "Add window_agg=mean as a candidate (nll, topk)")
    group.add_argument("--step_p_grid", type=float, nargs="+", default=None,
                       help="Step percentiles for anomalous runs (run_nll, run_rank; default: as p_grid of hids-calibrate)")
    group.add_argument("--calib_fraction", type=float, default=0.5, help="Share of test recordings in the calib part")
    group.add_argument("--split_seed", type=int, default=0, help="Seed for the calib/holdout split")

    group = parser.add_argument_group("Output")
    group.add_argument("--out_dir", type=str, default=None, help="Output directory (None -> {work_dir}/np/<service>)")
    group.add_argument("--cache", type=str, default=None,
                       help="Per-step score cache .npz (default: {out_dir}/cache_<service>.npz); "
                            "a hids-calibrate cache of the same checkpoint and data is reused")
    _add_bool(group, "--no_cache", False, "Ignore and overwrite the per-step score cache")

    _add_dir_args(parser, model_dir=True)
    _add_ram_args(parser)
    return parser


def _check_np_args(parser, args) -> None:
    if not all(0 < a < 1 for a in args.alphas):
        parser.error("--alphas: every value must satisfy 0 < alpha < 1")
    if args.auc_alpha not in args.alphas:
        parser.error("--auc_alpha must be one of --alphas")
    if not all(0 < q <= 1 for q in args.q_grid):
        parser.error("--q_grid: every value must satisfy 0 < q <= 1")
    if args.step_p_grid is not None and not all(0 < p < 100 for p in args.step_p_grid):
        parser.error("--step_p_grid: every value must satisfy 0 < p < 100")
    if not 0 < args.calib_fraction < 1:
        parser.error("--calib_fraction must satisfy 0 < calib_fraction < 1")


def np_threshold(val_scores: np.ndarray, alpha: float) -> tuple[float, float]:
    """Поріг Неймана-Пірсона за нормальними вікнами val: (τ, α').

    τ — найменше значення серед оцінок val, для якого частка вікон val з s > τ не перевищує α;
    α' — ця частка (досягнутий рівень, α' <= α). Без інтерполяції, тож для дискретних статистик
    з однаковими значеннями α' може бути помітно меншим за α: менший поріг дав би α' > α.
    Серед порогів з тією самою часткою на val найменший дає найбільше тривог на test.
    """
    s = np.sort(np.asarray(val_scores, dtype=np.float64))
    values = np.unique(s)
    above = len(s) - np.searchsorted(s, values, side="right")  # спадає; для максимуму — 0
    allowed = np.floor(alpha * len(s) + 1e-9)
    i = int(np.argmax(above <= allowed))
    return float(values[i]), float(above[i] / len(s))


def candidate_statistics(method, val_steps: np.ndarray, test_steps: np.ndarray, rows: list):
    """Кандидати гіперпараметра: (значення, оцінки вікон val, оцінки вікон test).

    Квантильні методи: s(w) = квантиль q кроків вікна (або mean). Серійні: s(w) = R, найдовша серія
    кроків з оцінкою > percentile(усіх кроків val, p); кроковий p — гіперпараметр, поріг вікна — τ над R.
    """
    for value in rows:
        if method.family == "quantile":
            yield value, aggregate(val_steps, value), aggregate(test_steps, value)
        else:
            tau_step = float(np.percentile(val_steps.ravel(), value))
            yield (value, max_run_length(val_steps > tau_step).astype(np.float64),
                   max_run_length(test_steps > tau_step).astype(np.float64))


def select_for_alpha(candidates: list[tuple], alpha: float, calib_attack: np.ndarray) -> dict:
    """Максимум recall на атакувальних вікнах calib при τ = np_threshold(val, α) кожного кандидата.

    candidates: (значення, оцінки вікон val, оцінки вікон test); calib_attack — маска атакувальних
    вікон calib серед вікон test. За рівного recall — менший α', далі перший кандидат.
    """
    best = None
    for value, val_s, test_s in candidates:
        tau, alpha_val = np_threshold(val_s, alpha)
        recall = float((test_s[calib_attack] > tau).mean())
        key = (recall, -alpha_val)
        if best is None or key > best["key"]:
            best = {"key": key, "value": value, "tau": tau, "alpha_val": alpha_val, "calib_recall": recall,
                    "test_scores": test_s}
    best.pop("key")
    return best


def holdout_metrics(test_s: np.ndarray, tau: float, ctx: dict) -> dict:
    """Метрики вікон holdout при порозі τ, ROC-AUC статистики і метрики на рівні записів holdout."""
    mask, is_attack = ctx["holdout_mask"], ctx["test_is_attack"]
    alarm = test_s > tau
    att, al = is_attack[mask], alarm[mask]
    tp, fp = int((al & att).sum()), int((al & ~att).sum())
    fn, tn = int(att.sum()) - tp, int((~att).sum()) - fp
    m = {k: float(v) for k, v in metrics_from_confusion(tp, fp, fn, tn, 1.0).items()
         if k in ("precision", "recall", "fpr", "f1")}
    alarmed, attack, delay = record_flags(alarm, is_attack, ctx["test_rec_idx"], ctx["test_t_end"], ctx["holdout_order"])
    rec = record_metrics(alarmed, attack, delay)
    return {
        **m, "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "roc_auc": float(roc_auc_score(att, test_s[mask])),
        "record_fpr": rec["normal_alarmed"], "record_recall": rec["attack_detected"],
        "n_normal_records": rec["n_normal_records"], "n_attack_records": rec["n_attack_records"],
    }


def _param(method, value, tau: float) -> dict:
    """Опис обраної точки: гіперпараметр і похідний поріг у зрозумілих одиницях (k для topk, m для серій)."""
    if method.family == "run":
        return {"param": "step_p", "value": float(value), "derived": f"m={int(np.floor(tau)) + 1}"}
    q = "mean" if value == "mean" else float(value)
    return {"param": "q", "value": q, "derived": f"k={int(np.floor(tau))}" if method.name == "topk" else ""}


def _pct(a: float) -> str:
    return f"{a * 100:g}%"


RESULT_FIELDS = [
    "service", "method", "alpha", "param", "value", "derived", "tau", "alpha_val", "calib_recall",
    "recall", "precision", "f1", "fpr", "roc_auc", "record_fpr", "record_recall",
    "n_normal_records", "n_attack_records", "tp", "fp", "fn", "tn",
]


def write_results_csv(path: str, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        writer.writerows({k: r[k] for k in RESULT_FIELDS} for r in rows)


def summary_table(rows: list[dict], alphas: list[float], auc_alpha: float) -> tuple[list[str], list[list]]:
    """Рядки — методи, стовпці — recall, precision і FPR записів при кожному α, плюс ROC-AUC (при auc_alpha)."""
    header = ["method"]
    for a in alphas:
        header += [f"recall@{_pct(a)}", f"precision@{_pct(a)}", f"record_fpr@{_pct(a)}"]
    header.append(f"roc_auc@{_pct(auc_alpha)}")
    by_key = {(r["method"], r["alpha"]): r for r in rows}
    table = []
    for method in dict.fromkeys(r["method"] for r in rows):
        line: list = [method]
        for a in alphas:
            r = by_key[(method, a)]
            line += [r["recall"], r["precision"], r["record_fpr"]]
        line.append(by_key[(method, auc_alpha)]["roc_auc"])
        table.append(line)
    return header, table


def log_table(header: list[str], table: list[list]) -> None:
    widths = [max(len(header[0]), *(len(t[0]) for t in table))] + [max(len(h), 6) for h in header[1:]]
    logging.info("  ".join(h.ljust(w) for h, w in zip(header, widths)))
    for t in table:
        logging.info("  ".join([t[0].ljust(widths[0])] + [f"{v:.3f}".ljust(w) for v, w in zip(t[1:], widths[1:])]))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = build_np_arg_parser(description=__doc__)
    args = parser.parse_args()
    _check_np_args(parser, args)
    args, input_log_messages = check_args(args)
    for message, level in input_log_messages:
        logging.log(level, message)
    resource_guard.configure(
        args.ram_guard_enabled, args.ram_soft_limit_percent, args.ram_hard_limit_percent, args.ram_throttle_sleep_sec
    )
    out_dir = args.out_dir or os.path.join(args.work_dir, "np", args.service)
    os.makedirs(out_dir, exist_ok=True)

    device = torch.device(args.device or ("cuda" if torch.cuda.is_available() else "cpu"))
    checkpoint_path = Path(args.checkpoint or os.path.join(args.model_dir, f"{args.service}.pt"))
    model, checkpoint = load_model(checkpoint_path.stem, device, str(checkpoint_path.parent))
    val_step = args.val_step or (checkpoint.get("train_args") or {}).get("seq_step")
    if val_step is None:
        parser.error("checkpoint has no train_args.seq_step: pass --val_step (the seq_step used in training)")
    seq_len = checkpoint["seq_len"]

    # кеш і його ключ — як у hids-calibrate, тож кеш hids-calibrate для того самого чекпоінта підходить
    val_files = recording_files(args.service, "val", args.dataset_root)
    normal_files, abnormal_files = test_recording_files(args.service, args.dataset_root)
    fingerprint = data_fingerprint(val_files + normal_files + abnormal_files, args.dataset_root)
    checkpoint_sha256 = sha256_file(str(checkpoint_path))
    cache_key = {
        "cache_version": CACHE_VERSION, "checkpoint_sha256": checkpoint_sha256,
        "val_step": int(val_step), "seq_len": int(seq_len), "data_fingerprint": fingerprint,
    }
    cache_path = args.cache or os.path.join(out_dir, f"cache_{args.service}.npz")
    if args.no_cache and os.path.exists(cache_path):
        os.remove(cache_path)
    cache, from_cache = load_or_compute_cache(
        cache_path, cache_key,
        lambda: compute_cache(model, checkpoint, args, val_files, normal_files, abnormal_files, val_step, device),
    )
    logging.info(f"Per-step NLL and ranks {'loaded from cache' if from_cache else 'computed and cached'}: {cache_path}")
    test_is_attack, test_rec_idx = cache["test_is_attack"], cache["test_rec_idx"]
    rec_is_attack = cache["test_rec_is_attack"]

    calib_recs, holdout_recs = split_recordings(rec_is_attack, args.calib_fraction, args.split_seed)
    calib_mask = np.isin(test_rec_idx, calib_recs)
    holdout_mask = ~calib_mask
    if not test_is_attack[calib_mask].any():
        raise SystemExit("calib has no attack windows: recall cannot be maximized")
    if test_is_attack[holdout_mask].all() or not test_is_attack[holdout_mask].any():
        raise SystemExit("holdout has only one window class: need at least 2 normal and 2 abnormal recordings")
    ctx = {
        "test_is_attack": test_is_attack, "test_rec_idx": test_rec_idx, "test_t_end": cache["test_t_end"],
        "holdout_mask": holdout_mask,
        "holdout_order": np.concatenate([holdout_recs[~rec_is_attack[holdout_recs]],
                                         holdout_recs[rec_is_attack[holdout_recs]]]),
    }
    calib_attack = calib_mask & test_is_attack
    logging.info(
        f"val windows: {len(cache['val_nll'])} (step {val_step}), test windows: {len(test_is_attack)}; "
        f"calib: {len(calib_recs)} recordings, holdout: {len(holdout_recs)} recordings"
    )

    steps = {"nll": (cache["val_nll"], cache["test_nll"]), "rank": (cache["val_rank"], cache["test_rank"])}
    q_rows: list = list(args.q_grid) + (["mean"] if args.include_mean else [])
    step_p_rows = [float(p) for p in (default_p_grid() if args.step_p_grid is None else sorted(args.step_p_grid))]
    alphas = sorted(set(args.alphas))

    rows: list[dict] = []
    for method in build_methods(args.methods):
        val_steps, test_steps = steps[method.step_key]
        candidates = list(candidate_statistics(
            method, val_steps, test_steps, q_rows if method.family == "quantile" else step_p_rows
        ))
        for alpha in alphas:
            sel = select_for_alpha(candidates, alpha, calib_attack)
            hold = holdout_metrics(sel["test_scores"], sel["tau"], ctx)
            row = {"service": args.service, "method": method.name, "alpha": alpha,
                   **_param(method, sel["value"], sel["tau"]),
                   "tau": sel["tau"], "alpha_val": sel["alpha_val"], "calib_recall": sel["calib_recall"], **hold}
            rows.append(row)
            logging.info(
                f"[{method.name} α={_pct(alpha)}] {row['param']}={row['value']} {row['derived']} τ={row['tau']:.4f} "
                f"α'(val)={row['alpha_val']:.4%} | holdout: recall={row['recall']:.3f} precision={row['precision']:.3f} "
                f"F1={row['f1']:.3f} FPR={row['fpr']:.4f} ROC-AUC={row['roc_auc']:.3f} "
                f"record FPR={row['record_fpr']:.3f} record recall={row['record_recall']:.3f}"
            )

    write_results_csv(os.path.join(out_dir, "np_results.csv"), rows)
    header, table = summary_table(rows, alphas, args.auc_alpha)
    with open(os.path.join(out_dir, "np_table.csv"), "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(table)
    with open(os.path.join(out_dir, "np_meta.json"), "w", encoding="utf-8") as fh:
        json.dump({
            "service": args.service, "checkpoint": {"path": str(checkpoint_path), "sha256": checkpoint_sha256},
            "git_commit": get_git_commit(), "data_fingerprint": fingerprint, "cache": cache_path,
            "alphas": alphas, "auc_alpha": args.auc_alpha, "split_seed": args.split_seed,
            "calib_fraction": args.calib_fraction, "val_step": int(val_step), "seq_len": int(seq_len),
            "q_grid": q_rows, "step_p_grid": step_p_rows,
            "split": {"calib": [str(cache["test_files"][r]) for r in calib_recs],
                      "holdout": [str(cache["test_files"][r]) for r in holdout_recs]},
        }, fh, indent=2, ensure_ascii=False)

    logging.info(f"\n[{args.service}] Neyman-Pearson: holdout metrics at fixed window alpha on val")
    log_table(header, table)
    logging.info(f"Results: {out_dir}")


if __name__ == "__main__":
    main()
