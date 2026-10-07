"""Калібрування методів оцінювання аномальності під F-beta: два параметри на метод, сітка на calib.

Чисті функції без вводу-виводу: усе працює з уже порахованими оцінками кроків
(NLL або ранг справжнього виклику, масиви [n_windows, seq_len]) і мітками вікон. Модель тут не потрібна.

Методи (Method): рішення для вікна завжди зводиться до «score > threshold», тому матриця помилок,
бутстреп, PR і ROC спільні для всіх методів.
- nll: оцінка кроку NLL, оцінка вікна — квантиль q кроків, поріг — перцентиль p оцінок вікон val;
- topk: те саме на рангах (див. quantile_operating_point);
- run_nll / run_rank: найдовша серія аномальних кроків у вікні, R >= m (див. run_grid_search).
"""

from dataclasses import dataclass
from typing import Any, Callable, Literal

import numpy as np
import torch

Agg = float | Literal["mean"]
StepKey = Literal["nll", "rank"]


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


def step_ranks(logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    """Ранг справжнього наступного виклику серед передбачень моделі: 1 + кількість класів зі строго
    більшим логітом. Нічия не підвищує ранг; 1 — модель вважала цей виклик найімовірнішим.

    logits [..., V], target [...] (індекси класів) -> int32 [...].
    """
    target_logit = logits.gather(-1, target.long().unsqueeze(-1))
    return ((logits > target_logit).sum(dim=-1) + 1).to(torch.int32)


def aggregate(step_nll: np.ndarray, q: Agg) -> np.ndarray:
    """Оцінка вікна з оцінок кроків: квантиль q по кроках (q=1.0 — максимум) або "mean"."""
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


def quantile_operating_point(val_steps: np.ndarray, test_steps: np.ndarray, q: Agg, p: float) -> tuple[np.ndarray, float]:
    """Оцінки вікон test і поріг θ = percentile(оцінок вікон val, p) для квантильних методів (nll, topk).

    Для topk кроки — ранги: ранги дискретні, тому на тепловій карті будуть сходинки й однакові пороги
    для сусідніх p (це очікувано). Ефективне k = ⌊θ⌋: вікно аномальне, якщо понад (1−q) частки
    викликів вікна не потрапили в top-k. Квантиль лінійно інтерполюється (та сама aggregate, що й для nll),
    тому це тлумачення точне, лише коли квантиль припадає на цілу позицію.
    """
    return aggregate(test_steps, q), float(np.percentile(aggregate(val_steps, q), p))


def max_run_length(anomalous: np.ndarray) -> np.ndarray:
    """Довжина найдовшої серії поспіль True у кожному рядку bool [N, L] -> int32 [N].

    Векторно по вікнах, цикл лише по L крокам. Серія не переходить межу вікна.
    """
    n, length = anomalous.shape
    cur = np.zeros(n, dtype=np.int32)
    best = np.zeros(n, dtype=np.int32)
    for t in range(length):
        cur = (cur + 1) * anomalous[:, t]
        np.maximum(best, cur, out=best)
    return best


def run_counts_all_m(run_len: np.ndarray, is_attack: np.ndarray, length: int) -> tuple[np.ndarray, np.ndarray]:
    """TP і FP для всіх m = 0..length одразу: вікно аномальне, якщо R >= m.

    Гістограма R за класами і накопичена сума з кінця: tp[m] = #атакувальних вікон з R >= m.
    """
    hist_attack = np.bincount(run_len[is_attack], minlength=length + 1)
    hist_normal = np.bincount(run_len[~is_attack], minlength=length + 1)
    return hist_attack[::-1].cumsum()[::-1], hist_normal[::-1].cumsum()[::-1]


def run_grid_search(
    val_steps: np.ndarray,
    test_steps: np.ndarray,
    test_is_attack: np.ndarray,
    rows: list[int],
    p_grid: np.ndarray,
    beta: float,
) -> dict[str, np.ndarray]:
    """Сітка (m, p) для методів серій (run_nll, run_rank).

    Крок аномальний, якщо його оцінка > τ = percentile(оцінок усіх кроків усіх вікон val, p).
    Оцінка вікна R — найдовша серія аномальних кроків поспіль; вікно аномальне, якщо R >= m
    (m відіграє роль порогу, перцентиль оцінок вікон не потрібен). Серії рахуються всередині вікна
    і не переходять межу вікон (test нарізаний без перекриття) — обмеження методу.
    Для рангів τ ціле, тож сусідні p часто дають той самий τ (сходинки на тепловій карті).

    Повертає масиви [len(rows), len(p_grid)]: threshold (= τ у кожному стовпці), tp, fp, fn, tn,
    precision, recall, fpr, f1, f{beta}, fbeta.
    """
    length = test_steps.shape[1]
    m_idx = np.asarray(rows, dtype=np.int64)
    n_attack = int(test_is_attack.sum())
    n_normal = len(test_is_attack) - n_attack
    taus = np.percentile(val_steps.ravel(), p_grid)
    tp = np.empty((len(rows), len(p_grid)), dtype=np.int64)
    fp = np.empty_like(tp)
    for j, tau in enumerate(taus):
        tp_all, fp_all = run_counts_all_m(max_run_length(test_steps > tau), test_is_attack, length)
        tp[:, j], fp[:, j] = tp_all[m_idx], fp_all[m_idx]
    fn, tn = n_attack - tp, n_normal - fp
    metrics = metrics_from_confusion(tp, fp, fn, tn, beta)
    threshold = np.broadcast_to(taus, tp.shape).astype(np.float64)
    return {"threshold": threshold, "tp": tp, "fp": fp, "fn": fn, "tn": tn, **metrics, "fbeta": metrics[f"f{beta:g}"]}


def run_operating_point(val_steps: np.ndarray, test_steps: np.ndarray, m: int, p: float) -> tuple[np.ndarray, float]:
    """Оцінки вікон test (R, як float) і поріг m − 0.5: для цілих R умова R >= m рівносильна R > m − 0.5."""
    tau = float(np.percentile(val_steps.ravel(), p))
    return max_run_length(test_steps > tau).astype(np.float64), m - 0.5


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


def edge_flags(selected: tuple[int, int], shape: tuple[int, int], mean_row: int | None = None) -> dict[str, bool]:
    """Чи обрана точка на краю сітки: row — перший або останній рядок параметра вікна
    (рядок "mean" окремий і краєм не вважається), col — перший або останній p."""
    i, j = selected
    n_rows = shape[0] - (1 if mean_row is not None else 0)
    return {"row": i != mean_row and i in (0, n_rows - 1), "col": j in (0, shape[1] - 1)}


def precision_at_prevalence(tpr, fpr, prevalence: float) -> np.ndarray:
    """Precision при частці атак prevalence: TPR·π / (TPR·π + FPR·(1−π))."""
    tpr = np.asarray(tpr, dtype=np.float64)
    fpr = np.asarray(fpr, dtype=np.float64)
    return _safe_div(tpr * prevalence, tpr * prevalence + fpr * (1 - prevalence))


def bootstrap_samples(n_normal: int, n_abnormal: int, n_boot: int, seed: int) -> np.ndarray:
    """Ресемпли записів з поверненням, normal і abnormal окремо: [n_boot, n_normal + n_abnormal].

    Індекси локальні в порядку [normal..., abnormal...]. Генеруються один раз і спільні для всіх методів,
    тому можна рахувати парні різниці метрик на тих самих ресемплах.
    """
    rng = np.random.default_rng(seed)
    picks = []
    for start, size in ((0, n_normal), (n_normal, n_abnormal)):
        if size:
            picks.append(start + rng.integers(0, size, size=(n_boot, size)))
    return np.concatenate(picks, axis=1)


def bootstrap_metrics(
    scores: np.ndarray,
    is_attack: np.ndarray,
    rec_idx: np.ndarray,
    recs: np.ndarray,
    threshold: float,
    sample: np.ndarray,
    beta: float,
) -> dict[str, np.ndarray]:
    """Метрики (precision, recall, fpr, f1, f{beta}) на кожному ресемплі [n_boot].

    recs — записи частини в тому самому порядку, що й локальні індекси sample. Вікна однієї записи йдуть разом.
    """
    pos = {int(r): i for i, r in enumerate(recs)}
    in_part = np.isin(rec_idx, recs)
    local = np.array([pos[int(r)] for r in rec_idx[in_part]], dtype=np.int64)
    above = scores[in_part] > threshold
    attack = is_attack[in_part]
    n_windows = np.bincount(local, minlength=len(recs))
    n_above = np.bincount(local, weights=above, minlength=len(recs))
    n_attack = np.bincount(local, weights=attack, minlength=len(recs))
    n_attack_above = np.bincount(local, weights=above & attack, minlength=len(recs))

    tp = n_attack_above[sample].sum(axis=1)
    fn = n_attack[sample].sum(axis=1) - tp
    fp = n_above[sample].sum(axis=1) - tp
    tn = n_windows[sample].sum(axis=1) - n_attack[sample].sum(axis=1) - fp
    return metrics_from_confusion(tp, fp, fn, tn, beta)


def ci95(values: np.ndarray) -> list[float]:
    lo, hi = np.percentile(values, [2.5, 97.5])
    return [float(lo), float(hi)]


def ci95_summary(boot: dict[str, np.ndarray], beta: float) -> dict[str, list[float]]:
    """95% бутстреп-інтервали F-beta, recall і FPR."""
    return {key: ci95(boot[key]) for key in (f"f{beta:g}", "recall", "fpr")}


def paired_delta_ci(boot_a: np.ndarray, boot_b: np.ndarray) -> dict:
    """95% інтервал парної різниці a − b на тих самих ресемплах; значуща, якщо інтервал не містить 0."""
    lo, hi = ci95(np.asarray(boot_a, dtype=np.float64) - np.asarray(boot_b, dtype=np.float64))
    return {"ci95": [lo, hi], "significant": not lo <= 0.0 <= hi}


@dataclass(frozen=True)
class Method:
    """Метод оцінювання аномальності з двома параметрами під калібрування (рядок сітки × перцентиль p)."""

    name: str  # nll | topk | run_nll | run_rank
    label: str  # підпис на графіках і в легендах
    family: Literal["quantile", "run"]
    step_key: StepKey  # яку матрицю кроків брати: NLL чи ранги
    row_param: str  # q | m
    col_param: str  # p
    row_axis: str
    col_axis: str
    title: str  # заголовок теплової карти; {f} -> назва F-метрики
    # (val_steps, test_steps, test_is_attack, rows, p_grid, beta) -> масиви [len(rows), len(p_grid)]
    search: Callable[[np.ndarray, np.ndarray, np.ndarray, list, np.ndarray, float], dict[str, np.ndarray]]
    # (val_steps, test_steps, значення рядка, p) -> (оцінки вікон test, поріг): тривога, якщо score > поріг
    operating_point: Callable[[np.ndarray, np.ndarray, Any, float], tuple[np.ndarray, float]]


METHOD_NAMES = ("nll", "topk", "run_nll", "run_rank")
METHOD_LABELS = {
    "nll": "NLL + квантиль вікна",
    "topk": "Ранг (top-k) + квантиль вікна",
    "run_nll": "Серія аномальних викликів (NLL)",
    "run_rank": "Серія аномальних викликів (ранг)",
}
_Q_AXIS = "Квантиль агрегації вікна, q"
_P_WINDOW_AXIS = "Перцентиль порогу на валідаційній вибірці, p"
_M_AXIS = "Мінімальна довжина серії, m"
_P_STEP_AXIS = "Перцентиль порогу аномального виклику на валідаційній вибірці, p"


def build_methods(names: list[str]) -> list[Method]:
    """Методи в порядку METHOD_NAMES (незалежно від порядку names)."""
    specs = {
        "nll": ("quantile", "nll", "Залежність {f} від параметрів агрегації та порогу"),
        "topk": ("quantile", "rank", "Залежність {f} від параметрів агрегації та порогу (оцінка кроку — ранг)"),
        "run_nll": ("run", "nll", "Залежність {f} від мінімальної довжини серії та порогу кроку (оцінка кроку — NLL)"),
        "run_rank": ("run", "rank", "Залежність {f} від мінімальної довжини серії та порогу кроку (оцінка кроку — ранг)"),
    }
    methods = []
    for name in METHOD_NAMES:
        if name not in names:
            continue
        family, step_key, title = specs[name]
        quantile = family == "quantile"
        methods.append(Method(
            name=name, label=METHOD_LABELS[name], family=family, step_key=step_key,
            row_param="q" if quantile else "m", col_param="p",
            row_axis=_Q_AXIS if quantile else _M_AXIS, col_axis=_P_WINDOW_AXIS if quantile else _P_STEP_AXIS,
            title=title,
            search=grid_search if quantile else run_grid_search,
            operating_point=quantile_operating_point if quantile else run_operating_point,
        ))
    return methods
