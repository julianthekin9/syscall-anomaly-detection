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
    aggregate,
    confusion_at_threshold,
    fbeta,
    grid_search,
    metrics_from_confusion,
    smooth_select,
    split_recordings,
)

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"


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


def test_calibrate_end_to_end(tmp_path: Path, monkeypatch) -> None:
    shutil.copytree(GOLDEN_DIR / "data" / "FIXT", tmp_path / "data" / "FIXT")
    out_dir = tmp_path / "out"
    model_dir = tmp_path / "models"
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    argv = [
        "hids-calibrate", "--service", "FIXT", "--checkpoint", str(GOLDEN_DIR / "FIXT.pt"),
        "--dataset_root", str(tmp_path / "data"), "--val_step", "32", "--out_dir", str(out_dir),
        "--model_dir", str(model_dir), "--bootstrap", "200", "--write_checkpoint",
    ]
    monkeypatch.setattr(sys, "argv", argv)
    calibrate.main()

    for name in ("calibration.json", "grid.csv", "f2_heatmap.png", "pr_curve_holdout.png", "cache_FIXT.npz"):
        assert (out_dir / name).exists(), name
    result = json.loads((out_dir / "calibration.json").read_text(encoding="utf-8"))
    for key in ("checkpoint", "git_commit", "split_seed","data_fingerprint", "split", "grid", "selected", "raw_max",
                "baseline", "sanity", "metrics", "attack_fraction_holdout", "prevalence_rescaled"):
        assert key in result, key
    assert result["sanity"]["threshold_match"] is True
    assert result["split_seed"] == 0
    calib, holdout = result["split"]["calib"], result["split"]["holdout"]
    assert not set(calib["normal"] + calib["abnormal"]) & set(holdout["normal"] + holdout["abnormal"])
    for name in ("selected", "baseline"):
        assert set(result["metrics"]["holdout"][name]["ci95"]) == {"f2", "recall", "fpr"}
        assert 0.0 <= result["metrics"]["holdout"][name]["roc_auc"] <= 1.0
    n_rows = len(result["grid"]["q"]) + 1
    n_lines = len((out_dir / "grid.csv").read_text(encoding="utf-8").strip().splitlines())
    assert n_lines == 1 + n_rows * 100

    # повторний запуск бере кеш і дає той самий результат
    mtime = (out_dir / "cache_FIXT.npz").stat().st_mtime_ns
    calibrate.main()
    assert (out_dir / "cache_FIXT.npz").stat().st_mtime_ns == mtime
    assert json.loads((out_dir / "calibration.json").read_text(encoding="utf-8"))["selected"] == result["selected"]

    # копія чекпоінта: нові агрегація й поріг, вихідний файл не змінено
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
