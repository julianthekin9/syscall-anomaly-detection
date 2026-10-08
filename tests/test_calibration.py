"""hids-calibrate: чисті функції tools/calibration.py та end-to-end на фікстурах tests/golden."""

import csv
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
from sklearn.metrics import balanced_accuracy_score, fbeta_score, matthews_corrcoef, roc_auc_score

from syscall_hids.cli import calibrate, eval_recordings
from syscall_hids.tools import evaluation
from syscall_hids.data.sequences import make_sequences
from syscall_hids.tools.calibration import (
    METHOD_NAMES,
    OBJECTIVE_KINDS,
    CriterionParams,
    Objective,
    aggregate,
    bootstrap_auc,
    bootstrap_metrics,
    bootstrap_samples,
    build_objectives,
    confusion_at_threshold,
    cost_metrics,
    criterion_value,
    default_p_grid,
    edge_flags,
    fbeta,
    grid_search,
    is_degenerate,
    max_run_length,
    metrics_from_confusion,
    objective_grid,
    paired_delta_ci,
    pauc,
    record_flags,
    record_metrics,
    run_counts_all_m,
    run_grid_search,
    run_operating_point,
    smooth_select,
    split_recordings,
    step_ranks,
    trivial_fbeta,
    trivial_values,
    window_starts,
)

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
REFERENCE = GOLDEN_DIR / "calibrate_reference.json"
RECALL_AT_FPR_REFERENCE = GOLDEN_DIR / "calibrate_recall_at_fpr_reference.json"


@pytest.mark.parametrize("beta", [0.5, 1.0, 2.0])
def test_fbeta_matches_sklearn(beta: float) -> None:
    rng = np.random.default_rng(0)
    for _ in range(20):
        y_true = rng.random(200) < 0.3
        y_pred = rng.random(200) < 0.4
        tp = int((y_true & y_pred).sum())
        fp = int((~y_true & y_pred).sum())
        fn = int((y_true & ~y_pred).sum())
        tn = int((~y_true & ~y_pred).sum())
        ours = metrics_from_confusion(tp, fp, fn, tn, beta)["fbeta"]
        assert float(ours) == pytest.approx(fbeta_score(y_true, y_pred, beta=beta, zero_division=0), abs=1e-12)
    assert float(fbeta(0.0, 0.0, 2.0)) == 0.0


def test_aggregate_max_and_median() -> None:
    step_nll = np.random.default_rng(1).random((50, 64)).astype(np.float32)
    np.testing.assert_allclose(aggregate(step_nll, 1.0), step_nll.max(axis=1))
    np.testing.assert_allclose(aggregate(step_nll, 0.5), np.median(step_nll, axis=1), rtol=1e-6)
    np.testing.assert_allclose(aggregate(step_nll, "mean"), step_nll.mean(axis=1), rtol=1e-6)


def test_split_recordings_deterministic_disjoint_stratified() -> None:
    rec_is_attack = np.array([False] * 7 + [True] * 5)
    calib_a, holdout_a = split_recordings(rec_is_attack, 0.5, seed=3)
    calib_b, holdout_b = split_recordings(rec_is_attack, 0.5, seed=3)
    np.testing.assert_array_equal(calib_a, calib_b)
    np.testing.assert_array_equal(holdout_a, holdout_b)
    assert not set(calib_a) & set(holdout_a)
    assert sorted(set(calib_a) | set(holdout_a)) == list(range(len(rec_is_attack)))
    for part in (calib_a, holdout_a):
        assert rec_is_attack[part].any() and not rec_is_attack[part].all()
    # інший seed дає інший поділ
    assert not np.array_equal(split_recordings(rec_is_attack, 0.5, seed=4)[0], calib_a)


def test_grid_search_beats_bad_threshold() -> None:
    rng = np.random.default_rng(0)
    val_nll = rng.normal(1.0, 0.3, size=(500, 16))
    normal = rng.normal(1.0, 0.3, size=(400, 16))
    attack = rng.normal(1.0, 0.3, size=(100, 16))
    attack[:, :4] += 2.5  # атака: кілька кроків із високим NLL
    test_nll = np.concatenate([normal, attack])
    is_attack = np.r_[np.zeros(400, bool), np.ones(100, bool)]
    rows = [0.5, 0.9, 1.0, "mean"]
    p_grid = np.round(np.arange(90.0, 99.95, 0.1), 6)

    grid = grid_search(val_nll, test_nll, is_attack, rows, p_grid, beta=2.0)
    assert grid["fbeta"].shape == (len(rows), len(p_grid))
    best = grid["fbeta"].max()
    # заздалегідь поганий поріг: вище за всі оцінки, жодної тривоги
    bad = confusion_at_threshold(aggregate(test_nll, 0.5), is_attack, [np.inf])
    bad_f2 = metrics_from_confusion(bad["tp"], bad["fp"], bad["fn"], bad["tn"], 2.0)["fbeta"][0]
    assert best > bad_f2 + 0.5


def test_smooth_select_prefers_plateau_over_spike() -> None:
    score = np.full((6, 20), 0.2)
    score[3:6, 12:17] = 0.7  # плато
    score[0, 2] = 0.95  # одиночний викид
    selected, raw, _ = smooth_select(score)
    assert raw == (0, 2)
    assert 3 <= selected[0] <= 5 and 12 <= selected[1] <= 16


def test_step_ranks_manual_and_ties() -> None:
    logits = torch.tensor([[[2.0, 1.0, 3.0, 0.5],      # ціль 2 — найбільший логіт: ранг 1
                            [2.0, 1.0, 3.0, 0.5],      # ціль 0: більший лише клас 2 -> ранг 2
                            [1.0, 1.0, 1.0, 0.0],      # нічия з двома класами не підвищує ранг -> 1
                            [0.0, 5.0, 4.0, -1.0]]])   # ціль 3: усі інші більші -> 4
    target = torch.tensor([[2, 0, 1, 3]])
    ranks = step_ranks(logits, target)
    assert ranks.dtype == torch.int32
    assert ranks.tolist() == [[1, 2, 1, 4]]
    # ранг за логітами збігається з рангом за log_softmax (монотонне перетворення)
    rng = torch.Generator().manual_seed(0)
    logits = torch.randn(3, 16, 30, generator=rng)
    target = torch.randint(0, 30, (3, 16), generator=rng)
    assert torch.equal(step_ranks(logits, target), step_ranks(torch.log_softmax(logits, dim=-1), target))


def _naive_max_run(row: np.ndarray) -> int:
    best = cur = 0
    for v in row:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return best


@pytest.mark.parametrize("length", [1, 7, 64])
@pytest.mark.parametrize("density", [0.0, 0.1, 0.5, 0.9, 1.0])
def test_max_run_length_matches_naive(length: int, density: float) -> None:
    b = np.random.default_rng(length).random((300, length)) < density
    expected = np.array([_naive_max_run(row) for row in b])
    np.testing.assert_array_equal(max_run_length(b), expected)


def test_run_counts_all_m_match_direct() -> None:
    rng = np.random.default_rng(2)
    length = 16
    run_len = rng.integers(0, length + 1, size=500)
    is_attack = rng.random(500) < 0.3
    tp, fp = run_counts_all_m(run_len, is_attack, length)
    for m in range(length + 1):
        assert tp[m] == int(((run_len >= m) & is_attack).sum())
        assert fp[m] == int(((run_len >= m) & ~is_attack).sum())


def test_run_grid_search_matches_operating_point() -> None:
    rng = np.random.default_rng(3)
    val = rng.normal(1.0, 0.3, size=(200, 16))
    test = rng.normal(1.0, 0.3, size=(120, 16))
    test[:40, 4:9] += 2.0  # атака: серія з 5 високих кроків
    is_attack = np.r_[np.ones(40, bool), np.zeros(80, bool)]
    rows, p_grid = [1, 2, 3, 5, 8], np.array([90.0, 95.0, 99.0])
    grid = run_grid_search(val, test, is_attack, rows, p_grid, beta=2.0)
    for i, m in enumerate(rows):
        for j, p in enumerate(p_grid):
            scores, thr = run_operating_point(val, test, m, p)
            conf = confusion_at_threshold(scores, is_attack, [thr])
            assert grid["tp"][i, j] == conf["tp"][0] and grid["fp"][i, j] == conf["fp"][0]
            assert grid["threshold"][i, j] == pytest.approx(np.percentile(val.ravel(), p))
    assert grid["fbeta"][rows.index(5), 0] > 0.9


def test_paired_bootstrap_self_difference_is_zero() -> None:
    rng = np.random.default_rng(4)
    rec_idx = np.repeat(np.arange(10), 6)
    is_attack = rec_idx >= 5
    scores = rng.random(len(rec_idx)) + is_attack * 0.3
    recs = np.arange(10)
    sample = bootstrap_samples(5, 5, 300, seed=0)
    assert sample.shape == (300, 10)
    assert (sample[:, :5] < 5).all() and (sample[:, 5:] >= 5).all()  # normal і abnormal ресемплуються окремо
    boot = bootstrap_metrics(scores, is_attack, rec_idx, recs, 0.6, sample, 2.0)
    delta = paired_delta_ci(boot["fbeta"], boot["fbeta"])
    assert delta == {"ci95": [0.0, 0.0], "significant": False}
    # той самий seed — ті самі ресемпли
    np.testing.assert_array_equal(bootstrap_samples(5, 5, 300, seed=0), sample)


def test_edge_flags() -> None:
    assert edge_flags((0, 5), (4, 10)) == {"row": True, "col": False}
    assert edge_flags((2, 9), (4, 10)) == {"row": False, "col": True}
    # рядок "mean" (останній) не є краєм; край квантильних рядків — передостанній
    assert edge_flags((3, 5), (4, 10), mean_row=3) == {"row": False, "col": False}
    assert edge_flags((2, 5), (4, 10), mean_row=3) == {"row": True, "col": False}


def _run_calibrate(monkeypatch, tmp_path: Path, extra: list[str]) -> Path:
    if not (tmp_path / "data" / "FIXT").exists():
        shutil.copytree(GOLDEN_DIR / "data" / "FIXT", tmp_path / "data" / "FIXT")
    out_dir = tmp_path / "out"
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    monkeypatch.setattr(sys, "argv", [
        "hids-calibrate", "--service", "FIXT", "--checkpoint", str(GOLDEN_DIR / "FIXT.pt"),
        "--dataset_root", str(tmp_path / "data"), "--val_step", "32", "--out_dir", str(out_dir),
        "--model_dir", str(tmp_path / "models"), "--bootstrap", "200", *extra,
    ])
    calibrate.main()
    return out_dir


def _assert_close(expected, actual, path: str = "") -> None:
    if isinstance(expected, dict):
        for key, value in expected.items():
            assert key in actual, f"{path}/{key}"
            _assert_close(value, actual[key], f"{path}/{key}")
    elif isinstance(expected, float):
        assert actual == pytest.approx(expected, rel=1e-9, abs=1e-12), path
    else:
        assert actual == expected, path


OBJECTIVE_TAGS = ("fbeta", "fbeta_fpr0.01", "fbeta_fpr0.05", "recall_at_fpr0.01", "recall_at_fpr0.05")


def _rename_f2(x):
    """Ключі версії до критеріїв: f2 -> fbeta, f2_smoothed -> score_smoothed (критерій fbeta)."""
    names = {"f2": "fbeta", "f2_smoothed": "score_smoothed"}
    if isinstance(x, dict):
        return {names.get(k, k): _rename_f2(v) for k, v in x.items()}
    return x


def test_calibrate_regression_beta2(tmp_path: Path, monkeypatch) -> None:
    """--beta 2 --objective fbeta з попередньою сіткою p відтворює calibration.json усіх методів версії 3f0eace."""
    old_p_grid = [f"{p:g}" for p in np.round(np.arange(90.0, 99.9 + 0.05, 0.1), 6)]
    out_dir = _run_calibrate(monkeypatch, tmp_path, ["--beta", "2", "--objective", "fbeta", "--p_grid", *old_p_grid])
    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
    for method in METHOD_NAMES:
        result = json.loads((out_dir / "fbeta" / method / "calibration.json").read_text(encoding="utf-8"))
        _assert_close(_rename_f2(reference[method]), result, method)
        assert result["beta"] == 2.0 and result["objective"]["tag"] == "fbeta"


def test_calibrate_end_to_end(tmp_path: Path, monkeypatch) -> None:
    out_dir = _run_calibrate(monkeypatch, tmp_path, [
        "--objective", "fbeta", "--objective", "recall_at_fpr", "--max_fpr", "0.01", "0.05", "--write_checkpoint",
    ])
    model_dir = tmp_path / "models"

    assert (out_dir / "cache_FIXT.npz").exists()
    assert (out_dir / "comparison.csv").exists() and (out_dir / "recall_at_fpr.png").exists()
    for tag in OBJECTIVE_TAGS:
        heatmap = "recall_heatmap.png" if tag.startswith("recall") else "f1_heatmap.png"
        for method in METHOD_NAMES:
            for name in ("calibration.json", "grid.csv", heatmap):
                assert (out_dir / tag / method / name).exists(), f"{tag}/{method}/{name}"
        for name in ("comparison.json", "f1_comparison.png", "pr_comparison.png", "roc_comparison.png"):
            assert (out_dir / tag / "comparison" / name).exists(), f"{tag}/{name}"

    result = json.loads((out_dir / "fbeta" / "nll" / "calibration.json").read_text(encoding="utf-8"))
    for key in ("method", "objective", "beta", "infeasible", "degenerate", "degenerate_holdout", "trivial_fbeta",
                "record_metrics", "checkpoint", "split", "grid", "selected", "raw_max", "baseline", "sanity", "metrics"):
        assert key in result, key
    assert result["beta"] == 1.0 and result["sanity"]["threshold_match"] is True
    assert result["trivial_fbeta"]["holdout"] == pytest.approx(2 * 0.5 / 1.5)  # F1 тривоги на все при pi = 0.5
    assert set(result["metrics"]["holdout"]["selected"]["ci95"]) == {"fbeta", "f1", "mcc", "youden", "recall", "fpr"}
    assert len(result["grid"]["p"]) == len(default_p_grid())
    for key in ("attack_detected", "normal_alarmed", "median_delay_sec", "ci95"):
        assert key in result["record_metrics"], key

    # обмеження FPR дотримано на calib
    for tag, limit in (("fbeta_fpr0.01", 0.01), ("fbeta_fpr0.05", 0.05), ("recall_at_fpr0.01", 0.01)):
        for method in METHOD_NAMES:
            r = json.loads((out_dir / tag / method / "calibration.json").read_text(encoding="utf-8"))
            assert r["infeasible"] or r["metrics"]["calib"]["selected"]["fpr"] <= limit, f"{tag}/{method}"

    comparison = json.loads((out_dir / "fbeta" / "comparison" / "comparison.json").read_text(encoding="utf-8"))
    assert [m["method"] for m in comparison["methods"]] == list(METHOD_NAMES)
    assert comparison["trivial"]["holdout"]["fbeta"] == pytest.approx(2 / 3)
    nll_entry = comparison["methods"][0]
    if not nll_entry["infeasible"]:
        assert nll_entry["delta_fbeta_vs_nll"] == {"value": 0.0, "ci95": [0.0, 0.0], "significant": False}
    tf = comparison["threshold_free"]
    assert [e["method"] for e in tf] == list(METHOD_NAMES)
    assert tf[0]["delta_pauc_vs_nll"] == {"value": 0.0, "ci95": [0.0, 0.0], "significant": False}
    for e in tf:
        assert 0.0 <= e["pauc"] <= 1.0 and 0.0 <= e["roc_auc"] <= 1.0

    rows = list(csv.DictReader((out_dir / "comparison.csv").open(encoding="utf-8")))
    assert len(rows) == len(OBJECTIVE_TAGS) * (3 + len(METHOD_NAMES))  # all_alarm, no_alarm, baseline, методи
    assert {r["method"] for r in rows} == {"all_alarm", "no_alarm", "baseline", *METHOD_NAMES}

    # регресія recall_at_fpr: обрані точки й метрики ті самі, що до узагальнення критеріїв
    # (прапор degenerate не порівнюється: його зміст для recall_at_fpr змінено навмисно)
    for key, expected in json.loads(RECALL_AT_FPR_REFERENCE.read_text(encoding="utf-8")).items():
        actual = json.loads((out_dir / key / "calibration.json").read_text(encoding="utf-8"))
        _assert_close(expected, actual, key)
    assert {r["objective"] for r in rows} == {"fbeta", "recall_at_fpr"}

    # повторний запуск бере кеш і дає той самий результат
    mtime = (out_dir / "cache_FIXT.npz").stat().st_mtime_ns
    calibrate.main()
    assert (out_dir / "cache_FIXT.npz").stat().st_mtime_ns == mtime
    again = json.loads((out_dir / "fbeta" / "nll" / "calibration.json").read_text(encoding="utf-8"))
    assert again["selected"] == result["selected"]

    # копія чекпоінта: nll з першого блоку критерію, вихідний файл не змінено
    calibrated = torch.load(model_dir / "FIXT_f2.pt", map_location="cpu")
    assert calibrated["threshold"] == pytest.approx(result["selected"]["threshold"])
    assert calibrated["calibration"]["selected"] == result["selected"]
    assert result["checkpoint"]["sha256"] == calibrate.sha256_file(str(GOLDEN_DIR / "FIXT.pt"))

    # hids-eval працює з копією
    reported: list[float] = []
    monkeypatch.setattr(evaluation, "plot_roc_curve", lambda truth, scores, service, auc, tags, plots_dir: reported.append(auc))
    monkeypatch.setattr(sys, "argv", [
        "hids-eval", "--service", "FIXT", "--checkpoint", str(model_dir / "FIXT_f2.pt"), "--eval-test-split",
        "--dataset_root", str(tmp_path / "data"), "--plots_dir", str(tmp_path / "plots"),
    ])
    eval_recordings.main()
    assert len(reported) == 1


def test_old_cache_is_recomputed(tmp_path: Path, monkeypatch) -> None:
    out_dir = _run_calibrate(monkeypatch, tmp_path, ["--methods", "nll", "--bootstrap", "0"])
    cache_path = out_dir / "cache_FIXT.npz"
    with np.load(cache_path, allow_pickle=False) as cached:
        old = {k: cached[k] for k in cached.files if k not in ("val_rank", "test_rank", "test_t_end")}
    old["cache_version"] = np.array(2)
    np.savez(cache_path, **old)

    _run_calibrate(monkeypatch, tmp_path, ["--methods", "run_rank", "--bootstrap", "0"])
    with np.load(cache_path, allow_pickle=False) as cached:
        assert int(cached["cache_version"]) == calibrate.CACHE_VERSION
        assert cached["test_rank"].dtype == np.int32 and cached["test_rank"].shape == cached["test_nll"].shape
        assert cached["test_t_end"].shape == (len(cached["test_nll"]),)
    comparison = json.loads((out_dir / "fbeta" / "comparison" / "comparison.json").read_text(encoding="utf-8"))
    assert comparison["reference_method"] is None and comparison["methods"][0]["delta_fbeta_vs_nll"] is None


def test_window_starts_match_make_sequences() -> None:
    seq_len = 8
    for n in [9, 10, 16, 17, 18, 25, 40, 64, 65, 100]:
        for step in (1, 3, seq_len):
            rows = np.arange(n, dtype=np.int16)[:, None]
            X, y = make_sequences(rows, seq_len, step)
            starts = window_starts(n, seq_len, step)
            assert len(starts) == len(X), (n, step)
            np.testing.assert_array_equal(X[:, 0, 0], starts)
            np.testing.assert_array_equal(y[:, -1, 0], starts + seq_len)  # остання ціль — строка s + seq_len
    assert len(window_starts(seq_len, seq_len, seq_len)) == 0


def test_default_p_grid() -> None:
    grid = default_p_grid()
    assert np.all(np.diff(grid) > 0)
    assert grid[0] == 90.0 and grid[-1] == pytest.approx(99.999)
    assert 99.0 in grid and 99.9 in grid and (grid > 99.9).sum() == 9
    assert np.allclose(np.diff(grid[grid <= 99.0]), 0.5)


def test_trivial_fbeta_formula() -> None:
    for pi in (0.1, 0.5, 0.9):
        y_true = np.r_[np.ones(int(pi * 1000), bool), np.zeros(1000 - int(pi * 1000), bool)]
        for beta in (1.0, 2.0):
            assert trivial_fbeta(pi, beta) == pytest.approx(fbeta_score(y_true, np.ones(1000, bool), beta=beta))


def test_build_objectives() -> None:
    tags = [o.tag for o in build_objectives(["fbeta", "recall_at_fpr"], [0.01, 0.05])]
    assert tags == ["fbeta", "fbeta_fpr0.01", "fbeta_fpr0.05", "recall_at_fpr0.01", "recall_at_fpr0.05"]
    # без --max_fpr: fbeta без обмеження, recall_at_fpr — 0.01 і 0.05 за замовчуванням
    assert [o.tag for o in build_objectives(["fbeta", "recall_at_fpr"], None)] == \
        ["fbeta", "recall_at_fpr0.01", "recall_at_fpr0.05"]


def _two_group_scores(rng, signal: bool):
    """Половина атак: 70% чітко вищі за норму (якщо signal), решта — як норма. pi = 0.5."""
    val = rng.normal(0.0, 1.0, size=(4000, 1))
    normal = rng.normal(0.0, 1.0, size=(2000, 1))
    attack = rng.normal(0.0, 1.0, size=(2000, 1))
    if signal:
        attack[:1400] += 6.0
    return val, np.concatenate([normal, attack]), np.r_[np.zeros(2000, bool), np.ones(2000, bool)]


P_LOW_HIGH = np.array([0.5, 1.0, 1.5, 2.0, 97.0, 98.0, 99.0, 99.5])


def _select(val, test, is_attack, objective: Objective, beta: float, p_grid=P_LOW_HIGH, params=None):
    params = params or CriterionParams(beta=beta)
    grid = grid_search(val, test, is_attack, [1.0], p_grid, beta)
    score, feasible, tiebreak, _ = objective_grid(grid, objective, params)
    return grid, smooth_select(score, None, feasible, tiebreak)


def _degenerate(grid, ij, objective: Objective, is_attack: np.ndarray, beta: float) -> bool:
    params = CriterionParams(beta=beta)
    conf = [grid[k][ij] for k in ("tp", "fp", "fn", "tn")]
    trivial = trivial_values(objective, int(is_attack.sum()), int((~is_attack).sum()), params)
    return is_degenerate(objective, criterion_value(objective, *conf, params), grid["fpr"][ij], trivial)


def test_f1_avoids_trivial_point_that_f2_prefers() -> None:
    val, test, is_attack = _two_group_scores(np.random.default_rng(0), signal=True)
    grid2, (sel2, _, _) = _select(val, test, is_attack, Objective("fbeta"), beta=2.0)
    grid1, (sel1, _, _) = _select(val, test, is_attack, Objective("fbeta"), beta=1.0)
    # F2: максимум у зоні «тривога майже на все», і вона вироджена
    assert grid2["fpr"][sel2] > 0.5
    assert _degenerate(grid2, sel2, Objective("fbeta"), is_attack, 2.0)
    # F1: змістовна точка з низьким FPR і F1 помітно вище тривіального рівня
    assert grid1["fpr"][sel1] < 0.05
    assert not _degenerate(grid1, sel1, Objective("fbeta"), is_attack, 1.0)


def test_degenerate_without_signal() -> None:
    val, test, is_attack = _two_group_scores(np.random.default_rng(1), signal=False)
    grid, (sel, _, _) = _select(val, test, is_attack, Objective("fbeta"), beta=1.0)
    assert _degenerate(grid, sel, Objective("fbeta"), is_attack, 1.0)


def test_max_fpr_constraint_for_every_criterion_and_infeasible() -> None:
    val, test, is_attack = _two_group_scores(np.random.default_rng(2), signal=True)
    for kind in OBJECTIVE_KINDS:
        grid, (sel, raw, _) = _select(val, test, is_attack, Objective(kind, 0.02), beta=1.0)
        assert grid["fpr"][sel] <= 0.02 and grid["fpr"][raw] <= 0.02, kind
    # лише низькі пороги (FPR ~ 0.98+): допустимих точок немає
    grid = grid_search(val, test, is_attack, [1.0], P_LOW_HIGH[:4], 1.0)
    score, feasible, tiebreak, _ = objective_grid(grid, Objective("fbeta", 0.01), CriterionParams())
    assert smooth_select(score, None, feasible, tiebreak) is None


def test_criteria_values_match_sklearn_and_manual() -> None:
    rng = np.random.default_rng(7)
    params = CriterionParams(beta=1.0, cost_fn=10.0, cost_fp=1.0)
    for _ in range(30):
        y_true = rng.random(300) < rng.uniform(0.1, 0.9)
        y_pred = rng.random(300) < rng.uniform(0.05, 0.95)
        tp, fp = int((y_true & y_pred).sum()), int((~y_true & y_pred).sum())
        fn, tn = int((y_true & ~y_pred).sum()), int((~y_true & ~y_pred).sum())
        tpr, fpr = tp / (tp + fn), fp / (fp + tn)
        value = lambda kind: criterion_value(Objective(kind), tp, fp, fn, tn, params)  # noqa: E731
        assert value("mcc") == pytest.approx(matthews_corrcoef(y_true, y_pred), abs=1e-12)
        assert value("youden") == pytest.approx(2 * balanced_accuracy_score(y_true, y_pred) - 1, abs=1e-12)
        assert value("gmean") == pytest.approx(np.sqrt(tpr * (1 - fpr)), abs=1e-12)
        assert value("eer") == pytest.approx(abs(fpr - (1 - tpr)), abs=1e-12)
        assert value("cost") == pytest.approx((10 * fn + fp) / 300, abs=1e-12)
        assert value("fbeta") == pytest.approx(fbeta_score(y_true, y_pred, beta=1.0, zero_division=0), abs=1e-12)
    # MCC з нульовим знаменником = 0 (усі передбачення одного класу)
    assert criterion_value(Objective("mcc"), 10, 5, 0, 0, params) == 0.0
    assert float(cost_metrics(1, 2, 3, 4, 10.0, 1.0)["cost_per_window"]) == pytest.approx(32 / 10)


def test_trivial_values_and_generalized_degenerate() -> None:
    params = CriterionParams(beta=1.0, cost_fn=10.0, cost_fp=1.0)
    t = lambda kind, limit=None: trivial_values(Objective(kind, limit), 60, 40, params)  # noqa: E731
    assert t("fbeta") == pytest.approx({"all_alarm": 0.75, "no_alarm": 0.0})
    for kind in ("youden", "mcc", "gmean"):
        assert t(kind) == pytest.approx({"all_alarm": 0.0, "no_alarm": 0.0}), kind
    assert t("eer") == pytest.approx({"all_alarm": 1.0, "no_alarm": 1.0})
    assert t("cost") == pytest.approx({"all_alarm": 0.4, "no_alarm": 6.0})
    # максимізація: не краще за найкращий тривіальний детектор більш ніж на margin
    assert is_degenerate(Objective("fbeta"), 0.70, 0.2, t("fbeta"))
    assert not is_degenerate(Objective("fbeta"), 0.80, 0.2, t("fbeta"))
    assert is_degenerate(Objective("youden"), 0.005, 0.2, t("youden"))
    assert not is_degenerate(Objective("youden"), 0.2, 0.2, t("youden"))
    # мінімізація (cost): найкращий тривіальний — «тривога на все» з вартістю 0.4 на вікно
    assert not is_degenerate(Objective("cost"), 0.30, 0.2, t("cost"))
    assert is_degenerate(Objective("cost"), 0.395, 0.2, t("cost"))
    # з обмеженням FPR «тривога на все» недопустима: recall порівнюється лише з «жодної тривоги» (0)
    assert not is_degenerate(Objective("recall_at_fpr", 0.05), 0.3, 0.04, t("recall_at_fpr", 0.05))
    assert is_degenerate(Objective("recall_at_fpr", 0.05), 0.005, 0.04, t("recall_at_fpr", 0.05))
    # FPR(calib) > 0.5 — вироджено незалежно від значення
    assert is_degenerate(Objective("youden"), 0.3, 0.6, t("youden"))


def _weak_signal_scores(rng, n: int = 20000, shift: float = 0.5):
    """Збалансований тест зі слабким сигналом: атаки ~ N(shift, 1), норма ~ N(0, 1)."""
    val = rng.normal(0.0, 1.0, size=(n, 1))
    test = np.concatenate([rng.normal(0.0, 1.0, size=(n, 1)), rng.normal(shift, 1.0, size=(n, 1))])
    return val, test, np.r_[np.zeros(n, bool), np.ones(n, bool)]


P_FINE = np.round(np.arange(1.0, 99.5 + 0.25, 0.5), 6)


def test_balanced_criteria_do_not_collapse_to_alarm_on_all() -> None:
    val, test, is_attack = _weak_signal_scores(np.random.default_rng(3))
    grid2, (sel2, _, _) = _select(val, test, is_attack, Objective("fbeta"), 2.0, P_FINE)
    assert grid2["fpr"][sel2] > 0.5 and _degenerate(grid2, sel2, Objective("fbeta"), is_attack, 2.0)
    for kind in ("youden", "gmean", "mcc"):
        grid, (sel, _, _) = _select(val, test, is_attack, Objective(kind), 1.0, P_FINE)
        assert grid["fpr"][sel] < 0.5, kind
        assert not _degenerate(grid, sel, Objective(kind), is_attack, 1.0), kind


def test_eer_point_has_equal_error_rates() -> None:
    val, test, is_attack = _weak_signal_scores(np.random.default_rng(4), n=50000, shift=1.0)
    grid, (_, raw, _) = _select(val, test, is_attack, Objective("eer"), 1.0, P_FINE)
    step = 0.005  # крок сітки p 0.5% ≈ крок FPR
    assert abs(grid["fpr"][raw] - grid["fnr"][raw]) < step
    assert grid["fpr"][raw] == pytest.approx(0.3085, abs=0.01)  # FPR = FNR = Φ(−0.5) для N(0,1) проти N(1,1)


def test_cost_with_equal_costs_minimizes_error_count() -> None:
    val, test, is_attack = _weak_signal_scores(np.random.default_rng(5))
    params = CriterionParams(cost_fn=1.0, cost_fp=1.0)
    grid, (_, raw, _) = _select(val, test, is_attack, Objective("cost"), 1.0, P_FINE, params)
    errors = grid["fn"] + grid["fp"]
    assert errors[raw] == errors.min()


def test_calibrate_all_criteria_end_to_end(tmp_path: Path, monkeypatch) -> None:
    out_dir = _run_calibrate(monkeypatch, tmp_path, [
        "--objective", "fbeta", "youden", "mcc", "gmean", "eer", "cost", "recall_at_fpr", "--max_fpr", "0.05",
        "--bootstrap", "50",
    ])
    kinds = ("fbeta", "youden", "mcc", "gmean", "eer", "cost")
    tags = [*kinds, *(f"{k}_fpr0.05" for k in kinds), "recall_at_fpr0.05"]
    for tag in tags:
        assert (out_dir / tag / "comparison" / "comparison.json").exists(), tag
        r = json.loads((out_dir / tag / "nll" / "calibration.json").read_text(encoding="utf-8"))
        expected_key = "recall_at_fpr" if tag.startswith("recall_at_fpr") else tag.removesuffix("_fpr0.05")
        assert r["criterion"]["key"] == expected_key
        assert set(r["trivial_criterion"]["holdout"]) == {"all_alarm", "no_alarm"}
        if not r["infeasible"]:
            for key in ("mcc", "youden", "gmean", "fnr", "cost", "cost_per_window"):
                assert key in r["metrics"]["holdout"]["selected"], (tag, key)
    for name in ("comparison.csv", "operating_points_roc.png", "criteria_comparison.png"):
        assert (out_dir / name).exists(), name
    rows = list(csv.DictReader((out_dir / "comparison.csv").open(encoding="utf-8")))
    assert len(rows) == len(tags) * (3 + len(METHOD_NAMES))
    assert {r["service"] for r in rows} == {"FIXT"}
    for col in ("mcc", "youden", "gmean", "cost", "cost_per_window", "criterion_value", "f1_lo", "mcc_hi"):
        assert col in rows[0], col





def test_smooth_select_feasible_mask_and_tiebreak() -> None:
    score = np.full((3, 6), 0.3)
    score[1, 4] = 0.9  # найкраща точка, але недопустима
    feasible = np.ones((3, 6), bool)
    feasible[1, 4] = False
    (sel, raw, smoothed) = smooth_select(score, None, feasible)
    assert sel != (1, 4) and raw != (1, 4)
    assert np.isclose(smoothed[1, 3], 0.3)  # недопустимий сусід не впливає на згладження
    # tiebreak: за рівного значення — менший FPR
    recall = np.full((1, 4), 0.5)
    fpr = np.array([[0.04, 0.01, 0.03, 0.02]])
    (sel, _, _) = smooth_select(recall, None, None, fpr)
    assert sel == (0, 1)


def test_pauc_matches_sklearn_and_unit_bootstrap() -> None:
    rng = np.random.default_rng(5)
    rec_idx = np.repeat(np.arange(8), 50)
    is_attack = rec_idx >= 4
    scores = rng.normal(size=len(rec_idx)) + is_attack * 0.8
    assert pauc(is_attack, scores) == pytest.approx(roc_auc_score(is_attack, scores, max_fpr=0.05))
    identity = np.arange(8)[None, :]  # ресемпл, де кожна запис узята рівно один раз
    assert bootstrap_auc(scores, is_attack, rec_idx, np.arange(8), identity)[0] == pytest.approx(pauc(is_attack, scores))


def test_record_metrics_manual() -> None:
    # записи 0,1 — нормальні; 2,3,4 — атакувальні; по 3 вікна, t_end = 1, 2, 3 с
    rec_idx = np.repeat(np.arange(5), 3)
    is_attack = rec_idx >= 2
    t_end = np.tile([1.0, 2.0, 3.0], 5)
    alarm = np.zeros(15, bool)
    alarm[1] = True  # нормальна 0: тривога
    alarm[[7, 8]] = True  # атака 2: перша тривога на 2-му вікні (2 с)
    alarm[[9]] = True  # атака 3: перша тривога на 1-му вікні (1 с); атака 4 без тривог
    alarmed, attack, delay = record_flags(alarm, is_attack, rec_idx, t_end, np.arange(5))
    m = record_metrics(alarmed, attack, delay)
    assert m["attack_detected"] == pytest.approx(2 / 3)
    assert m["normal_alarmed"] == pytest.approx(1 / 2)
    assert m["median_delay_sec"] == pytest.approx(1.5)
    assert (m["n_attack_records"], m["n_detected"], m["n_normal_records"]) == (3, 2, 2)


def test_write_checkpoint_requires_nll(tmp_path: Path, monkeypatch) -> None:
    with pytest.raises(SystemExit):
        _run_calibrate(monkeypatch, tmp_path, ["--methods", "topk", "--write_checkpoint"])
