"""Калібрування методів оцінювання аномальності під F-beta: два параметри на метод, сітка на calib.

Чисті функції без вводу-виводу: усе працює з уже порахованими оцінками кроків
(NLL або ранг справжнього виклику, масиви [n_windows, seq_len]) і мітками вікон. Модель тут не потрібна.

Методи (Method): рішення для вікна завжди зводиться до «score > threshold», тому матриця помилок,
бутстреп, PR і ROC спільні для всіх методів.
- nll: оцінка кроку NLL, оцінка вікна — квантиль q кроків, поріг — перцентиль p оцінок вікон val;
- topk: те саме на рангах (див. quantile_operating_point);
- run_nll / run_rank: найдовша серія аномальних кроків у вікні, R >= m (див. run_grid_search).
"""

import warnings
from dataclasses import dataclass
from typing import Any, Callable, Literal

import numpy as np
import torch
from sklearn.metrics import roc_auc_score

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


def mcc(tp, fp, fn, tn) -> np.ndarray:
    """Коефіцієнт кореляції Метьюза; 0 при нульовому знаменнику (як sklearn.matthews_corrcoef)."""
    tp, fp, fn, tn = (np.asarray(v, dtype=np.float64) for v in (tp, fp, fn, tn))
    den = np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return _safe_div(tp * tn - fp * fn, den)


def metrics_from_confusion(tp, fp, fn, tn, beta: float) -> dict[str, np.ndarray]:
    """Метрики з матриці помилок (векторно): precision, recall (TPR), fpr, fnr, f1, fbeta, mcc,
    youden (J = TPR − FPR), gmean (√(TPR·TNR)), balanced_accuracy."""
    precision = _safe_div(tp, np.asarray(tp) + np.asarray(fp))
    recall = _safe_div(tp, np.asarray(tp) + np.asarray(fn))
    fpr = _safe_div(fp, np.asarray(fp) + np.asarray(tn))
    return {
        "precision": precision,
        "recall": recall,
        "fpr": fpr,
        "f1": fbeta(precision, recall, 1.0),
        "fbeta": fbeta(precision, recall, beta),
        "fnr": 1.0 - recall,
        "mcc": mcc(tp, fp, fn, tn),
        "youden": recall - fpr,
        "gmean": np.sqrt(recall * (1.0 - fpr)),
        "balanced_accuracy": (recall + 1.0 - fpr) / 2.0,
    }


def cost_metrics(tp, fp, fn, tn, cost_fn: float, cost_fp: float) -> dict[str, np.ndarray]:
    """Вартість помилок c_fn·FN + c_fp·FP: повна і на одне вікно (порівнянна між частинами різного розміру)."""
    fp, fn = np.asarray(fp, dtype=np.float64), np.asarray(fn, dtype=np.float64)
    total = cost_fn * fn + cost_fp * fp
    return {"cost": total, "cost_per_window": _safe_div(total, np.asarray(tp) + fp + fn + np.asarray(tn))}


def trivial_fbeta(pi: float, beta: float) -> float:
    """F-beta детектора «тривога на кожне вікно» при частці атак pi: recall = 1, precision = pi."""
    b2 = beta * beta
    return float((1 + b2) * pi / (b2 * pi + 1)) if pi > 0 else 0.0


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
    recall, fpr, f1, fbeta.
    """
    out: dict[str, list[np.ndarray]] = {}
    for q in rows:
        thresholds = np.percentile(aggregate(val_nll, q), p_grid)
        conf = confusion_at_threshold(aggregate(test_nll, q), test_is_attack, thresholds)
        metrics = metrics_from_confusion(conf["tp"], conf["fp"], conf["fn"], conf["tn"], beta)
        for key, value in {"threshold": thresholds, **conf, **metrics}.items():
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
    precision, recall, fpr, f1, fbeta.
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
    return {"threshold": threshold, "tp": tp, "fp": fp, "fn": fn, "tn": tn, **metrics}


def run_operating_point(val_steps: np.ndarray, test_steps: np.ndarray, m: int, p: float) -> tuple[np.ndarray, float]:
    """Оцінки вікон test (R, як float) і поріг m − 0.5: для цілих R умова R >= m рівносильна R > m − 0.5."""
    tau = float(np.percentile(val_steps.ravel(), p))
    return max_run_length(test_steps > tau).astype(np.float64), m - 0.5


def _box_mean(values: np.ndarray, size_rows: int, size_cols: int, mask: np.ndarray | None = None) -> np.ndarray:
    """Середнє по околу size_rows×size_cols лише по наявних і допустимих (mask) сусідах; без сусідів — nan."""
    if mask is None:
        mask = np.ones_like(values)
    pr, pc = size_rows // 2, size_cols // 2
    padded = np.pad(np.where(mask > 0, values, 0.0), ((pr, pr), (pc, pc)))
    counts = np.pad(mask.astype(values.dtype), ((pr, pr), (pc, pc)))
    total = np.zeros_like(values)
    n = np.zeros_like(values)
    rows, cols = values.shape
    for dr in range(size_rows):
        for dc in range(size_cols):
            total += padded[dr : dr + rows, dc : dc + cols]
            n += counts[dr : dr + rows, dc : dc + cols]
    return np.divide(total, n, out=np.full_like(values, np.nan), where=n > 0)


def _argmax_with_tiebreak(values: np.ndarray, allowed: np.ndarray, tiebreak: np.ndarray | None) -> tuple[int, int]:
    """argmax серед allowed; за рівного значення — мінімальний tiebreak (без tiebreak — перший, як np.argmax)."""
    masked = np.where(allowed, values, -np.inf)
    if tiebreak is None:
        idx = np.unravel_index(int(np.argmax(masked)), values.shape)
    else:
        best = masked.max()
        candidates = np.where(masked >= best - 1e-12, np.asarray(tiebreak, dtype=np.float64), np.inf)
        idx = np.unravel_index(int(np.argmin(candidates)), values.shape)
    return int(idx[0]), int(idx[1])


def smooth_select(
    score: np.ndarray,
    mean_row: int | None = None,
    feasible: np.ndarray | None = None,
    tiebreak: np.ndarray | None = None,
) -> tuple[tuple[int, int], tuple[int, int], np.ndarray] | None:
    """Стійкий вибір точки сітки: argmax середнього по околу 3×3.

    Рядок "mean" (mean_row) не є сусідом квантильних рядків, тому згладжується лише вздовж осі p.
    feasible — маска допустимих точок (напр. FPR(calib) <= max_fpr): згладжування лише по допустимих
    сусідах, вибір і сирий максимум — лише серед допустимих. tiebreak — за рівного значення обирається
    точка з меншим tiebreak (напр. FPR). Сусідство береться в індексах сітки (сітка p нерівномірна).
    Повертає (обрана точка, сирий максимум, згладжена сітка) або None, якщо допустимих точок немає.
    """
    score = np.asarray(score, dtype=np.float64)
    allowed = np.ones(score.shape, dtype=bool) if feasible is None else np.asarray(feasible, dtype=bool)
    if not allowed.any():
        return None
    mask = None if feasible is None else allowed.astype(np.float64)
    smoothed = np.empty_like(score)
    q_rows = [i for i in range(score.shape[0]) if i != mean_row]
    if q_rows:
        smoothed[q_rows] = _box_mean(score[q_rows], 3, 3, None if mask is None else mask[q_rows])
    if mean_row is not None:
        smoothed[[mean_row]] = _box_mean(score[[mean_row]], 1, 3, None if mask is None else mask[[mean_row]])
    selected = _argmax_with_tiebreak(smoothed, allowed, tiebreak)
    raw = _argmax_with_tiebreak(score, allowed, tiebreak)
    return selected, raw, smoothed


@dataclass(frozen=True)
class CriterionParams:
    """Параметри критеріїв: beta (F-beta), prevalence (перерахунок precision), вартості помилок для cost."""

    beta: float = 1.0
    prevalence: float = 0.01
    cost_fn: float = 10.0
    cost_fp: float = 1.0


@dataclass(frozen=True)
class Criterion:
    """Критерій вибору робочої точки: значення з TP/FP/FN/TN (векторно по сітці) і напрям оптимізації.

    tiebreak — другорядний ключ (мінімізується) за рівного значення критерію.
    """

    key: str
    maximize: bool
    value: Callable[..., np.ndarray]  # (tp, fp, fn, tn, params) -> значення
    tiebreak: Callable[..., np.ndarray] | None = None  # (tp, fp, fn, tn) -> ключ
    needs_limit: bool = False  # лише разом з max_fpr (recall_at_fpr)


def _m(tp, fp, fn, tn, params: CriterionParams) -> dict[str, np.ndarray]:
    return metrics_from_confusion(tp, fp, fn, tn, params.beta)


def _fbeta_prevalence(tp, fp, fn, tn, params: CriterionParams) -> np.ndarray:
    m = _m(tp, fp, fn, tn, params)
    return fbeta(precision_at_prevalence(m["recall"], m["fpr"], params.prevalence), m["recall"], params.beta)


def _eer_gap(tp, fp, fn, tn, params: CriterionParams) -> np.ndarray:
    m = _m(tp, fp, fn, tn, params)
    return np.abs(m["fpr"] - m["fnr"])


def _error_sum(tp, fp, fn, tn) -> np.ndarray:
    m = metrics_from_confusion(tp, fp, fn, tn, 1.0)
    return m["fpr"] + m["fnr"]


def _fpr(tp, fp, fn, tn) -> np.ndarray:
    return metrics_from_confusion(tp, fp, fn, tn, 1.0)["fpr"]


CRITERIA: dict[str, Criterion] = {
    "fbeta": Criterion("fbeta", True, lambda tp, fp, fn, tn, p: _m(tp, fp, fn, tn, p)["fbeta"]),
    "fbeta_prevalence": Criterion("fbeta_prevalence", True, _fbeta_prevalence),
    "recall_at_fpr": Criterion("recall_at_fpr", True, lambda tp, fp, fn, tn, p: _m(tp, fp, fn, tn, p)["recall"],
                               tiebreak=_fpr, needs_limit=True),
    "youden": Criterion("youden", True, lambda tp, fp, fn, tn, p: _m(tp, fp, fn, tn, p)["youden"]),
    "mcc": Criterion("mcc", True, lambda tp, fp, fn, tn, p: _m(tp, fp, fn, tn, p)["mcc"]),
    "gmean": Criterion("gmean", True, lambda tp, fp, fn, tn, p: _m(tp, fp, fn, tn, p)["gmean"]),
    "eer": Criterion("eer", False, _eer_gap, tiebreak=_error_sum),
    "cost": Criterion("cost", False,
                      lambda tp, fp, fn, tn, p: cost_metrics(tp, fp, fn, tn, p.cost_fn, p.cost_fp)["cost_per_window"]),
}
OBJECTIVE_KINDS = tuple(CRITERIA)


def criterion_label_uk(kind: str, beta: float = 1.0, max_fpr: float | None = None) -> str:
    """Українська назва критерію (для графіків), з обмеженням FPR, якщо воно є."""
    labels = {
        "fbeta": f"F{beta:g}",
        "fbeta_prevalence": f"F{beta:g} з перерахунком на частку атак",
        "recall_at_fpr": "Повнота при FPR ≤ α" if max_fpr is None else f"Повнота при FPR ≤ {max_fpr:g}",
        "youden": "Індекс Юдена",
        "mcc": "Коефіцієнт кореляції Метьюза (MCC)",
        "gmean": "Середнє геометричне (G-mean)",
        "eer": "Точка рівних помилок (EER)",
        "cost": "Мінімум вартості помилок",
    }
    label = labels[kind]
    return label if max_fpr is None or kind == "recall_at_fpr" else f"{label}, FPR ≤ {max_fpr:g}"


@dataclass(frozen=True)
class Objective:
    """Критерій вибору робочої точки на calib (ключ CRITERIA) з необов'язковим обмеженням FPR(calib) <= max_fpr.

    fbeta — максимум F-beta; fbeta_prevalence — F-beta, перерахований на --prevalence; recall_at_fpr — максимум
    recall при FPR <= max_fpr (за рівного recall — менший FPR); youden — J = TPR − FPR (≡ balanced accuracy);
    mcc — коефіцієнт Метьюза; gmean — √(TPR·TNR); eer — мінімум |FPR − FNR| (за рівності — менша сума);
    cost — мінімум (c_fn·FN + c_fp·FP) / N.
    """

    kind: str
    max_fpr: float | None = None

    @property
    def criterion(self) -> Criterion:
        return CRITERIA[self.kind]

    @property
    def tag(self) -> str:
        if self.kind == "recall_at_fpr":
            return f"recall_at_fpr{self.max_fpr:g}"
        return self.kind + ("" if self.max_fpr is None else f"_fpr{self.max_fpr:g}")


RECALL_AT_FPR_DEFAULT = (0.01, 0.05)


def build_objectives(kinds: list[str], max_fprs: list[float] | None) -> list[Objective]:
    """Кожен критерій: блок без обмеження + блок на кожне max_fpr; recall_at_fpr — лише блоки з max_fpr.

    max_fprs = None (не задано): критерії без обмеження, recall_at_fpr — RECALL_AT_FPR_DEFAULT.
    """
    out: list[Objective] = []
    for kind in dict.fromkeys(kinds):
        needs_limit = CRITERIA[kind].needs_limit
        limits = list(max_fprs) if max_fprs is not None else (list(RECALL_AT_FPR_DEFAULT) if needs_limit else [])
        if not needs_limit:
            out.append(Objective(kind))
        out += [Objective(kind, float(f)) for f in limits]
    return out


def objective_grid(
    grid: dict[str, np.ndarray], objective: Objective, params: CriterionParams
) -> tuple[np.ndarray, np.ndarray | None, np.ndarray | None, np.ndarray]:
    """Для сітки calib: (оцінка для максимізації, маска допустимості або None, tiebreak або None, значення критерію).

    Оцінка для максимізації = значення критерію або −значення для критеріїв, що мінімізуються (eer, cost);
    далі smooth_select однаковий для всіх критеріїв.
    """
    c = objective.criterion
    conf = (grid["tp"], grid["fp"], grid["fn"], grid["tn"])
    value = np.asarray(c.value(*conf, params), dtype=np.float64)
    score = value if c.maximize else -value
    tiebreak = None if c.tiebreak is None else c.tiebreak(*conf)
    feasible = None if objective.max_fpr is None else grid["fpr"] <= objective.max_fpr
    return score, feasible, tiebreak, value


def criterion_value(objective: Objective, tp, fp, fn, tn, params: CriterionParams) -> float:
    """Значення критерію для однієї матриці помилок."""
    return float(objective.criterion.value(*(np.asarray([v]) for v in (tp, fp, fn, tn)), params)[0])


def trivial_values(objective: Objective, n_attack: int, n_normal: int, params: CriterionParams) -> dict[str, float]:
    """Значення критерію в тривіальних детекторів: «тривога на кожне вікно» і «жодної тривоги»."""
    return {
        "all_alarm": criterion_value(objective, n_attack, n_normal, 0, 0, params),
        "no_alarm": criterion_value(objective, 0, 0, n_attack, n_normal, params),
    }


def is_degenerate(objective: Objective, value: float, fpr: float, trivial: dict[str, float], margin: float = 0.01) -> bool:
    """Точка не краща за тривіальні детектори: FPR(calib) > 0.5 або значення критерію не краще за найкращий
    допустимий тривіальний детектор більш ніж на margin (в одиницях критерію, з урахуванням напряму).

    Допустимий — той, що проходить обмеження max_fpr: «тривога на все» (FPR = 1) при обмеженні випадає.
    Для youden, gmean і mcc обидва тривіальні значення дорівнюють 0, тому на збалансованому тесті ці критерії
    у «тривогу на все» не вироджуються (на відміну від F-beta, у якого «тривога на все» дає (1+β²)π/(β²π+1)).
    """
    sign = 1.0 if objective.criterion.maximize else -1.0
    candidates = [trivial["no_alarm"]] + ([trivial["all_alarm"]] if objective.max_fpr is None else [])
    best = max(sign * v for v in candidates)
    return bool(fpr > 0.5 or sign * value <= best + margin)


def default_p_grid() -> np.ndarray:
    """90–99 крок 0.5, 99.1–99.9 крок 0.1, далі 99.9–99.999 логарифмічно за часткою 100 − p (без повтору 99.9).

    Для обмеження FPR <= 1% потрібні пороги вище 99.9: у серійних методів при m = 1 частка тривог
    на нормальному вікні ≈ 1 − (p/100)^L.
    """
    coarse = np.arange(90.0, 99.0 + 0.25, 0.5)
    fine = np.arange(99.1, 99.9 + 0.05, 0.1)
    tail = 100.0 - np.logspace(np.log10(0.1), np.log10(0.001), 10)[1:]
    return np.round(np.concatenate([coarse, fine, tail]), 6)


def window_starts(n: int, seq_len: int, step: int) -> np.ndarray:
    """Індекси першої строки кожного вікна — та сама формула, що в data.sequences.make_sequences.

    Вікно зі стартом s займає строки s..s+seq_len (входи s..s+seq_len−1, цілі s+1..s+seq_len);
    останнє вікно притиснуте до кінця. Тест звіряє з вмістом вікон make_sequences.
    """
    needed = seq_len + 1
    if n < needed:
        return np.empty(0, dtype=np.int64)
    starts = list(range(0, n - needed + 1, step))
    if starts[-1] + needed < n:
        starts.append(n - needed)
    return np.asarray(starts, dtype=np.int64)


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


def ci95_summary(boot: dict[str, np.ndarray]) -> dict[str, list[float]]:
    """95% бутстреп-інтервали F-beta, F1, MCC, індексу Юдена, recall і FPR."""
    return {key: ci95(boot[key]) for key in ("fbeta", "f1", "mcc", "youden", "recall", "fpr")}


def paired_delta_ci(boot_a: np.ndarray, boot_b: np.ndarray) -> dict:
    """95% інтервал парної різниці a − b на тих самих ресемплах; значуща, якщо інтервал не містить 0."""
    lo, hi = ci95(np.asarray(boot_a, dtype=np.float64) - np.asarray(boot_b, dtype=np.float64))
    return {"ci95": [lo, hi], "significant": not lo <= 0.0 <= hi}


PAUC_MAX_FPR = 0.05


def pauc(is_attack: np.ndarray, scores: np.ndarray, sample_weight: np.ndarray | None = None,
         max_fpr: float = PAUC_MAX_FPR) -> float:
    """Часткова ROC-AUC при FPR <= max_fpr зі стандартизацією McClish (sklearn roc_auc_score(max_fpr=...))."""
    return float(roc_auc_score(is_attack, scores, sample_weight=sample_weight, max_fpr=max_fpr))


def _local_index(rec_idx: np.ndarray, recs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(маска вікон, що належать recs; локальний індекс записи в порядку recs для цих вікон)."""
    pos = np.full(int(max(rec_idx.max(), recs.max())) + 1, -1, dtype=np.int64)
    pos[recs] = np.arange(len(recs))
    in_part = pos[rec_idx] >= 0
    return in_part, pos[rec_idx[in_part]]


def bootstrap_auc(
    scores: np.ndarray, is_attack: np.ndarray, rec_idx: np.ndarray, recs: np.ndarray, sample: np.ndarray,
    max_fpr: float | None = PAUC_MAX_FPR,
) -> np.ndarray:
    """(p)AUC на кожному ресемплі [n_boot]: вага вікна = кратність його записи в ресемплі."""
    in_part, local = _local_index(rec_idx, recs)
    sc, att = scores[in_part], is_attack[in_part]
    out = np.empty(len(sample))
    for b, picks in enumerate(sample):
        w = np.bincount(picks, minlength=len(recs))[local].astype(np.float64)
        keep = w > 0
        out[b] = roc_auc_score(att[keep], sc[keep], sample_weight=w[keep], max_fpr=max_fpr)
    return out


def record_flags(
    alarm: np.ndarray, is_attack: np.ndarray, rec_idx: np.ndarray, t_end: np.ndarray, recs: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Для кожної записи recs: (є хоч одна тривога, запис атакувальний, затримка першої тривоги в с або nan).

    Затримка — t_end першого тривожного вікна від початку файлу; атакувальний файл починається з експлойту
    (так ріже конвертер), тож це затримка від початку атаки.
    """
    in_part, local = _local_index(rec_idx, recs)
    n = len(recs)
    alarmed = np.bincount(local, weights=alarm[in_part], minlength=n) > 0
    attack = np.bincount(local, weights=is_attack[in_part], minlength=n) > 0
    delay = np.full(n, np.inf)
    a_local, a_t = local[alarm[in_part]], t_end[in_part][alarm[in_part]]
    np.minimum.at(delay, a_local, a_t.astype(np.float64))
    delay[~np.isfinite(delay)] = np.nan
    return alarmed, attack, delay


def record_metrics(alarmed: np.ndarray, attack: np.ndarray, delay: np.ndarray) -> dict:
    """Частка атакувальних записів з тривогою, частка нормальних записів з тривогою, медіана затримки."""
    detected = alarmed & attack
    return {
        "attack_detected": float(alarmed[attack].mean()) if attack.any() else 0.0,
        "normal_alarmed": float(alarmed[~attack].mean()) if (~attack).any() else 0.0,
        "median_delay_sec": float(np.median(delay[detected])) if detected.any() else None,
        "n_attack_records": int(attack.sum()),
        "n_detected": int(detected.sum()),
        "n_normal_records": int((~attack).sum()),
    }


def bootstrap_record_metrics(alarmed: np.ndarray, attack: np.ndarray, delay: np.ndarray, sample: np.ndarray) -> dict:
    """95% ДІ метрик записів на спільних ресемплах (sample — локальні індекси тих самих recs)."""
    a, d = alarmed[sample], attack[sample]
    with np.errstate(invalid="ignore", divide="ignore"):
        det = (a & d).sum(1) / d.sum(1)
        norm = (a & ~d).sum(1) / (~d).sum(1)
    delays = np.where(a & d, delay[sample], np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # ресемпл без виявлених атак -> nan
        med = np.nanmedian(delays, axis=1)
    out = {}
    for key, values in (("attack_detected", det), ("normal_alarmed", norm), ("median_delay_sec", med)):
        values = values[np.isfinite(values)]
        out[key] = ci95(values) if len(values) else None
    return out


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


def curve_scores(method: Method, val_steps: np.ndarray, test_steps: np.ndarray, param) -> np.ndarray:
    """Оцінки вікон для ROC без вибору порогу: квантильні методи — aggregate(test, q);
    серійні — R при кроковому порозі τ = percentile(кроків val, p)."""
    if method.family == "quantile":
        return aggregate(test_steps, param)
    tau = float(np.percentile(val_steps.ravel(), param))
    return max_run_length(test_steps > tau).astype(np.float64)


def select_curve_param(
    method: Method, val_steps: np.ndarray, test_steps: np.ndarray, is_attack: np.ndarray, rows: list, p_grid: np.ndarray,
    max_fpr: float = PAUC_MAX_FPR,
) -> tuple[Any, float]:
    """Параметр кривої з максимумом pAUC на calib: q (квантильні) або кроковий p (серійні). -> (параметр, pAUC calib)."""
    if method.family == "quantile":
        candidates = [(q, aggregate(test_steps, q)) for q in rows]
    else:
        taus = np.percentile(val_steps.ravel(), p_grid)
        candidates = [(float(p), max_run_length(test_steps > tau).astype(np.float64)) for p, tau in zip(p_grid, taus)]
    best_param, best = None, -np.inf
    for param, scores in candidates:
        value = pauc(is_attack, scores, max_fpr=max_fpr)
        if value > best:
            best_param, best = param, value
    return best_param, float(best)
