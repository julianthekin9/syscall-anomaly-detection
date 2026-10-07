"""Калібрування агрегації вікна (q) і перцентиля порогу (p) під F-beta.

Чисті функції без вводу-виводу: усе працює з уже порахованими NLL на кожному кроці
(масиви [n_windows, seq_len]) і мітками вікон. Модель тут не потрібна.
"""

from typing import Literal

import numpy as np

Agg = float | Literal["mean"]


def split_recordings(rec_is_attack: np.ndarray, calib_fraction: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Стратифікований поділ записів на calib і holdout (індекси записів, відсортовані).

    Normal і abnormal перемішуються окремо; у кожній групі з n >= 2 записів
    обидві частини отримують хоча б один запис.
    """
    rng = np.random.default_rng(seed)
    calib_parts: list[np.ndarray] = []
    holdout_parts: list[np.ndarray] = []
    for group in (False, True):
        ids = np.flatnonzero(rec_is_attack == group)
        ids = ids[rng.permutation(len(ids))]
        n_calib = int(round(len(ids) * calib_fraction))
        if len(ids) >= 2:
            n_calib = min(max(n_calib, 1), len(ids) - 1)
        calib_parts.append(ids[:n_calib])
        holdout_parts.append(ids[n_calib:])
    return np.sort(np.concatenate(calib_parts)), np.sort(np.concatenate(holdout_parts))


def aggregate(step_nll: np.ndarray, q: Agg) -> np.ndarray:
    """Оцінка вікна з NLL на кроках: квантиль q по кроках (q=1.0 — максимум) або "mean"."""
    if q == "mean":
        return step_nll.mean(axis=1)
    return np.quantile(step_nll, q, axis=1)


def confusion_at_threshold(scores: np.ndarray, is_attack: np.ndarray, thresholds) -> dict[str, np.ndarray]:
    """TP, FP, FN, TN для кожного порогу (вікно — атака, якщо score > threshold)."""
    thresholds = np.asarray(thresholds, dtype=np.float64)
    attack_sorted = np.sort(scores[is_attack])
    normal_sorted = np.sort(scores[~is_attack])
    tp = len(attack_sorted) - np.searchsorted(attack_sorted, thresholds, side="right")
    fp = len(normal_sorted) - np.searchsorted(normal_sorted, thresholds, side="right")
    return {"tp": tp, "fp": fp, "fn": len(attack_sorted) - tp, "tn": len(normal_sorted) - fp}


def _safe_div(num, den) -> np.ndarray:
    num = np.asarray(num, dtype=np.float64)
    den = np.asarray(den, dtype=np.float64)
    return np.divide(num, den, out=np.zeros(np.broadcast(num, den).shape), where=den > 0)


def fbeta(p, r, beta: float) -> np.ndarray:
    """F-beta з precision і recall; 0, якщо обидві нульові (zero_division=0, як у sklearn)."""
    p = np.asarray(p, dtype=np.float64)
    r = np.asarray(r, dtype=np.float64)
    b2 = beta * beta
    return _safe_div((1 + b2) * p * r, b2 * p + r)


def metrics_from_confusion(tp, fp, fn, tn, beta: float) -> dict[str, np.ndarray]:
    precision = _safe_div(tp, np.asarray(tp) + np.asarray(fp))
    recall = _safe_div(tp, np.asarray(tp) + np.asarray(fn))
    fpr = _safe_div(fp, np.asarray(fp) + np.asarray(tn))
    return {
        "precision": precision,
        "recall": recall,
        "fpr": fpr,
        "f1": fbeta(precision, recall, 1.0),
        f"f{beta:g}": fbeta(precision, recall, beta),
    }


def grid_search(
    val_nll: np.ndarray,
    test_nll: np.ndarray,
    test_is_attack: np.ndarray,
    rows: list[Agg],
    p_grid: np.ndarray,
    beta: float,
) -> dict[str, np.ndarray]:
    """Сітка (рядок агрегації, p): поріг = percentile(val-оцінок, p), метрики на test-вікнах.

    Повертає масиви форми [len(rows), len(p_grid)]: threshold, tp, fp, fn, tn, precision,
    recall, fpr, f1, f{beta} (ключ "fbeta" дублює останній).
    """
    out: dict[str, list[np.ndarray]] = {}
    for q in rows:
        thresholds = np.percentile(aggregate(val_nll, q), p_grid)
        conf = confusion_at_threshold(aggregate(test_nll, q), test_is_attack, thresholds)
        metrics = metrics_from_confusion(conf["tp"], conf["fp"], conf["fn"], conf["tn"], beta)
        for key, value in {"threshold": thresholds, **conf, **metrics, "fbeta": metrics[f"f{beta:g}"]}.items():
            out.setdefault(key, []).append(np.asarray(value))
    return {key: np.stack(values) for key, values in out.items()}


def _box_mean(values: np.ndarray, size_rows: int, size_cols: int) -> np.ndarray:
    """Середнє по околу size_rows×size_cols; на краях — лише по наявних сусідах."""
    pr, pc = size_rows // 2, size_cols // 2
    padded = np.pad(values, ((pr, pr), (pc, pc)))
    counts = np.pad(np.ones_like(values), ((pr, pr), (pc, pc)))
    total = np.zeros_like(values)
    n = np.zeros_like(values)
    rows, cols = values.shape
    for dr in range(size_rows):
        for dc in range(size_cols):
            total += padded[dr : dr + rows, dc : dc + cols]
            n += counts[dr : dr + rows, dc : dc + cols]
    return total / n


def smooth_select(
    score: np.ndarray, mean_row: int | None = None
) -> tuple[tuple[int, int], tuple[int, int], np.ndarray]:
    """Стійкий вибір точки сітки: argmax середнього по околу 3×3.

    Рядок "mean" (mean_row) не є сусідом квантильних рядків, тому згладжується лише вздовж осі p.
    Повертає (обрана точка, сирий максимум, згладжена сітка).
    """
    score = np.asarray(score, dtype=np.float64)
    smoothed = np.empty_like(score)
    q_rows = [i for i in range(score.shape[0]) if i != mean_row]
    if q_rows:
        smoothed[q_rows] = _box_mean(score[q_rows], 3, 3)
    if mean_row is not None:
        smoothed[[mean_row]] = _box_mean(score[[mean_row]], 1, 3)
    selected = np.unravel_index(int(np.argmax(smoothed)), score.shape)
    raw = np.unravel_index(int(np.argmax(score)), score.shape)
    return (int(selected[0]), int(selected[1])), (int(raw[0]), int(raw[1])), smoothed


def precision_at_prevalence(tpr, fpr, prevalence: float) -> np.ndarray:
    """Precision при частці атак prevalence: TPR·π / (TPR·π + FPR·(1−π))."""
    tpr = np.asarray(tpr, dtype=np.float64)
    fpr = np.asarray(fpr, dtype=np.float64)
    return _safe_div(tpr * prevalence, tpr * prevalence + fpr * (1 - prevalence))


def bootstrap_ci(
    scores: np.ndarray,
    is_attack: np.ndarray,
    rec_idx: np.ndarray,
    normal_recs: np.ndarray,
    abnormal_recs: np.ndarray,
    threshold: float,
    n_boot: int,
    seed: int,
    beta: float,
) -> dict[str, list[float]]:
    """95% бутстреп-інтервали F-beta, recall і FPR: ресемплінг записів з поверненням,
    normal і abnormal окремо. Вікна однієї записи йдуть разом."""
    all_recs = np.concatenate([normal_recs, abnormal_recs])
    pos = {int(r): i for i, r in enumerate(all_recs)}
    in_part = np.isin(rec_idx, all_recs)
    local = np.array([pos[int(r)] for r in rec_idx[in_part]], dtype=np.int64)
    above = scores[in_part] > threshold
    attack = is_attack[in_part]
    n_windows = np.bincount(local, minlength=len(all_recs))
    n_above = np.bincount(local, weights=above, minlength=len(all_recs))
    n_attack = np.bincount(local, weights=attack, minlength=len(all_recs))
    n_attack_above = np.bincount(local, weights=above & attack, minlength=len(all_recs))

    rng = np.random.default_rng(seed)
    n_normal = len(normal_recs)
    picks = []
    for start, size in ((0, n_normal), (n_normal, len(abnormal_recs))):
        if size:
            picks.append(start + rng.integers(0, size, size=(n_boot, size)))
    sample = np.concatenate(picks, axis=1)  # [n_boot, n_recs]

    tp = n_attack_above[sample].sum(axis=1)
    fn = n_attack[sample].sum(axis=1) - tp
    fp = n_above[sample].sum(axis=1) - tp
    tn = n_windows[sample].sum(axis=1) - n_attack[sample].sum(axis=1) - fp
    metrics = metrics_from_confusion(tp, fp, fn, tn, beta)
    out = {}
    for key, name in ((f"f{beta:g}", f"f{beta:g}"), ("recall", "recall"), ("fpr", "fpr")):
        lo, hi = np.percentile(metrics[key], [2.5, 97.5])
        out[name] = [float(lo), float(hi)]
    return out
