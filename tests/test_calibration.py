"""hids-calibrate: чисті функції tools/calibration.py та end-to-end на фікстурах tests/golden."""

import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
from sklearn.metrics import fbeta_score

from syscall_hids.cli import calibrate, eval_recordings
from syscall_hids.tools import evaluation
from syscall_hids.tools.calibration import (
    METHOD_NAMES,
    aggregate,
    bootstrap_metrics,
    bootstrap_samples,
    confusion_at_threshold,
    edge_flags,
    fbeta,
    grid_search,
    max_run_length,
    metrics_from_confusion,
    paired_delta_ci,
    run_counts_all_m,
    run_grid_search,
    run_operating_point,
    smooth_select,
    split_recordings,
    step_ranks,
)

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
NLL_REFERENCE = GOLDEN_DIR / "calibrate_nll_reference.json"


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
        ours = metrics_from_confusion(tp, fp, fn, tn, beta)[f"f{beta:g}"]
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
    bad_f2 = metrics_from_confusion(bad["tp"], bad["fp"], bad["fn"], bad["tn"], 2.0)["f2"][0]
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
    delta = paired_delta_ci(boot["f2"], boot["f2"])
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


def test_calibrate_end_to_end(tmp_path: Path, monkeypatch) -> None:
    out_dir = _run_calibrate(monkeypatch, tmp_path, ["--methods", *METHOD_NAMES, "--write_checkpoint"])
    model_dir = tmp_path / "models"

    assert (out_dir / "cache_FIXT.npz").exists()
    for method in METHOD_NAMES:
        for name in ("calibration.json", "grid.csv", "f2_heatmap.png", "pr_curve_holdout.png"):
            assert (out_dir / method / name).exists(), f"{method}/{name}"
    for name in ("comparison.json", "comparison.csv", "f2_comparison.png", "pr_comparison.png", "roc_comparison.png"):
        assert (out_dir / "comparison" / name).exists(), name

    # регресія: nll збігається з результатом версії до додавання методів
    result = json.loads((out_dir / "nll" / "calibration.json").read_text(encoding="utf-8"))
    _assert_close(json.loads(NLL_REFERENCE.read_text(encoding="utf-8")), result)
    for key in ("method", "row_param", "col_param", "checkpoint", "git_commit", "split_seed", "data_fingerprint",
                "split", "grid", "selected", "raw_max", "baseline", "sanity", "metrics", "attack_fraction_holdout",
                "prevalence_rescaled"):
        assert key in result, key
    assert (result["method"], result["row_param"], result["col_param"]) == ("nll", "q", "p")
    assert result["sanity"]["threshold_match"] is True
    calib, holdout = result["split"]["calib"], result["split"]["holdout"]
    assert not set(calib["normal"] + calib["abnormal"]) & set(holdout["normal"] + holdout["abnormal"])
    for name in ("selected", "baseline"):
        assert set(result["metrics"]["holdout"][name]["ci95"]) == {"f2", "recall", "fpr"}
    n_rows = len(result["grid"]["q"]) + 1
    assert len((out_dir / "nll" / "grid.csv").read_text(encoding="utf-8").strip().splitlines()) == 1 + n_rows * 100

    # інші методи: власні параметри, той самий поділ, без базової лінії
    for method in ("topk", "run_nll", "run_rank"):
        other = json.loads((out_dir / method / "calibration.json").read_text(encoding="utf-8"))
        assert other["method"] == method and other["baseline"] is None
        assert other["split"] == result["split"]
        assert set(other["metrics"]["holdout"]) == {"selected"}
    run = json.loads((out_dir / "run_rank" / "calibration.json").read_text(encoding="utf-8"))
    assert run["row_param"] == "m" and {"m", "p", "tau", "k_eff", "on_edge"} <= set(run["selected"])
    run_header = (out_dir / "run_nll" / "grid.csv").read_text(encoding="utf-8").splitlines()[0]
    assert run_header.startswith("m,p,tau,tp,")
    assert "k_eff" in (out_dir / "topk" / "grid.csv").read_text(encoding="utf-8").splitlines()[0]

    comparison = json.loads((out_dir / "comparison" / "comparison.json").read_text(encoding="utf-8"))
    assert [m["method"] for m in comparison["methods"]] == list(METHOD_NAMES)
    assert comparison["reference_method"] == "nll" and comparison["bootstrap"]["shared_resamples"] is True
    nll_entry = comparison["methods"][0]
    assert nll_entry["delta_f2_vs_nll"] == {"value": 0.0, "ci95": [0.0, 0.0], "significant": False}
    assert nll_entry["holdout"]["f2"] == pytest.approx(result["metrics"]["holdout"]["selected"]["f2"])
    for entry in comparison["methods"]:
        assert 0.0 <= entry["holdout"]["roc_auc"] <= 1.0
        assert set(entry["holdout"]["ci95"]) == {"f2", "recall", "fpr"}
    assert comparison["baseline"]["holdout"]["f2"] == pytest.approx(result["metrics"]["holdout"]["baseline"]["f2"])
    csv_lines = (out_dir / "comparison" / "comparison.csv").read_text(encoding="utf-8").strip().splitlines()
    assert len(csv_lines) == 1 + 1 + len(METHOD_NAMES)  # шапка, базова лінія, методи

    # повторний запуск бере кеш і дає той самий результат
    mtime = (out_dir / "cache_FIXT.npz").stat().st_mtime_ns
    calibrate.main()
    assert (out_dir / "cache_FIXT.npz").stat().st_mtime_ns == mtime
    assert json.loads((out_dir / "nll" / "calibration.json").read_text(encoding="utf-8"))["selected"] == result["selected"]

    # копія чекпоінта: лише nll, нові агрегація й поріг, вихідний файл не змінено
    calibrated = torch.load(model_dir / "FIXT_f2.pt", map_location="cpu")
    assert calibrated["threshold"] == pytest.approx(result["selected"]["threshold"])
    assert calibrated["calibration"]["selected"] == result["selected"]
    assert calibrated["calibration"]["method"] == "nll"
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


def test_old_cache_without_ranks_is_recomputed(tmp_path: Path, monkeypatch) -> None:
    out_dir = _run_calibrate(monkeypatch, tmp_path, ["--methods", "nll", "--bootstrap", "0"])
    cache_path = out_dir / "cache_FIXT.npz"
    with np.load(cache_path, allow_pickle=False) as cached:
        old = {k: cached[k] for k in cached.files if k not in ("val_rank", "test_rank")}
    old["cache_version"] = np.array(1)
    np.savez(cache_path, **old)

    _run_calibrate(monkeypatch, tmp_path, ["--methods", "run_rank", "--bootstrap", "0"])
    with np.load(cache_path, allow_pickle=False) as cached:
        assert int(cached["cache_version"]) == calibrate.CACHE_VERSION
        assert cached["test_rank"].dtype == np.int32 and cached["test_rank"].shape == cached["test_nll"].shape
    comparison = json.loads((out_dir / "comparison" / "comparison.json").read_text(encoding="utf-8"))
    assert comparison["reference_method"] is None and comparison["methods"][0]["delta_f2_vs_nll"] is None


def test_write_checkpoint_requires_nll(tmp_path: Path, monkeypatch) -> None:
    with pytest.raises(SystemExit):
        _run_calibrate(monkeypatch, tmp_path, ["--methods", "topk", "--write_checkpoint"])
