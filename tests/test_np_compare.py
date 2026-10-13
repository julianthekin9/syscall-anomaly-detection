"""hids-np: поріг Неймана-Пірсона, вибір гіперпараметра за recall і end-to-end на фікстурах tests/golden."""

import csv
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

from syscall_hids.cli import calibrate, np_compare
from syscall_hids.cli.np_compare import np_threshold, select_for_alpha
from syscall_hids.tools.calibration import METHOD_NAMES

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"


def test_np_threshold_continuous() -> None:
    rng = np.random.default_rng(0)
    for n in (150, 1000, 9999):
        s = rng.normal(size=n)
        for alpha in (0.001, 0.01, 0.05):
            tau, alpha_val = np_threshold(s, alpha)
            assert alpha_val == (s > tau).mean() <= alpha
            # найменший такий поріг: наступне значення вниз уже перевищує α
            below = s[s < tau]
            if len(below):
                assert (s > below.max()).mean() > alpha


def test_np_threshold_ties_never_exceed_alpha() -> None:
    """97% вікон — 0, 3% — 1: при α=1% тривога неможлива (α'=0), при α=5% поріг 0 (α'=3%)."""
    s = np.r_[np.zeros(970), np.ones(30)]
    assert np_threshold(s, 0.01) == (1.0, 0.0)
    assert np_threshold(s, 0.05) == (0.0, 0.03)
    # np.percentile з інтерполяцією на 150 різних значеннях перевищує α, np_threshold — ні
    u = np.arange(150, dtype=float)
    tau_interp = np.percentile(u, 99.0)
    assert (u > tau_interp).mean() > 0.01
    tau, alpha_val = np_threshold(u, 0.01)
    assert alpha_val == 1 / 150 and tau == 148.0


def test_select_for_alpha_maximizes_recall_and_breaks_ties_by_alpha_val() -> None:
    val = np.arange(100, dtype=float)
    attack = np.ones(4, dtype=bool)
    weak = ("weak", val, np.array([0.0, 0.0, 200.0, 200.0]))
    strong = ("strong", val, np.array([200.0, 200.0, 200.0, 0.0]))
    assert select_for_alpha([weak, strong], 0.05, attack)["value"] == "strong"
    # той самий recall: обирається кандидат з меншим α' на val
    coarse_val = np.r_[np.zeros(96), np.ones(4)]  # α=5% -> τ=0, α'=4%
    fine_val = np.r_[np.zeros(99), np.ones(1)]  # α=5% -> τ=0, α'=1%
    test = np.array([2.0, 2.0, 2.0, 2.0])
    sel = select_for_alpha([("coarse", coarse_val, test), ("fine", fine_val, test)], 0.05, attack)
    assert sel["value"] == "fine" and sel["alpha_val"] == 0.01 and sel["calib_recall"] == 1.0


def _prepare(tmp_path: Path, monkeypatch) -> None:
    if not (tmp_path / "data" / "FIXT").exists():
        shutil.copytree(GOLDEN_DIR / "data" / "FIXT", tmp_path / "data" / "FIXT")
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)


def _run_np(monkeypatch, tmp_path: Path, extra: list[str]) -> Path:
    out_dir = tmp_path / "np"
    monkeypatch.setattr(sys, "argv", [
        "hids-np", "--service", "FIXT", "--checkpoint", str(GOLDEN_DIR / "FIXT.pt"),
        "--dataset_root", str(tmp_path / "data"), "--val_step", "32", "--out_dir", str(out_dir),
        "--model_dir", str(tmp_path / "models"), *extra,
    ])
    np_compare.main()
    return out_dir


def test_np_end_to_end(tmp_path: Path, monkeypatch) -> None:
    _prepare(tmp_path, monkeypatch)
    out_dir = _run_np(monkeypatch, tmp_path, [])
    with open(out_dir / "np_results.csv", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == len(METHOD_NAMES) * 3
    for r in rows:
        assert float(r["alpha_val"]) <= float(r["alpha"])
        for key in ("recall", "precision", "f1", "fpr", "roc_auc", "record_fpr", "record_recall"):
            assert 0.0 <= float(r[key]) <= 1.0
    with open(out_dir / "np_table.csv", encoding="utf-8") as fh:
        table = list(csv.reader(fh))
    assert table[0] == ["method", "recall@0.1%", "precision@0.1%", "record_fpr@0.1%", "recall@1%", "precision@1%",
                        "record_fpr@1%", "recall@5%", "precision@5%", "record_fpr@5%", "roc_auc@1%"]
    assert [t[0] for t in table[1:]] == list(METHOD_NAMES)
    meta = json.loads((out_dir / "np_meta.json").read_text(encoding="utf-8"))
    assert meta["alphas"] == [0.001, 0.01, 0.05]


def test_np_reuses_calibrate_cache_and_split(tmp_path: Path, monkeypatch) -> None:
    """Кеш hids-calibrate підходить для hids-np, а поділ calib/holdout той самий."""
    _prepare(tmp_path, monkeypatch)
    calib_dir = tmp_path / "calib"
    monkeypatch.setattr(sys, "argv", [
        "hids-calibrate", "--service", "FIXT", "--checkpoint", str(GOLDEN_DIR / "FIXT.pt"),
        "--dataset_root", str(tmp_path / "data"), "--val_step", "32", "--out_dir", str(calib_dir),
        "--model_dir", str(tmp_path / "models"), "--bootstrap", "0", "--methods", "nll",
    ])
    calibrate.main()
    cache = calib_dir / "cache_FIXT.npz"
    mtime = cache.stat().st_mtime_ns
    out_dir = _run_np(monkeypatch, tmp_path, ["--cache", str(cache), "--methods", "nll"])
    assert cache.stat().st_mtime_ns == mtime
    meta = json.loads((out_dir / "np_meta.json").read_text(encoding="utf-8"))
    calib_result = json.loads((calib_dir / "fbeta" / "nll" / "calibration.json").read_text(encoding="utf-8"))
    split = calib_result["split"]
    assert sorted(meta["split"]["calib"]) == sorted(split["calib"]["normal"] + split["calib"]["abnormal"])
    assert sorted(meta["split"]["holdout"]) == sorted(split["holdout"]["normal"] + split["holdout"]["abnormal"])


def test_np_args_validation(tmp_path: Path, monkeypatch) -> None:
    _prepare(tmp_path, monkeypatch)
    with pytest.raises(SystemExit):
        _run_np(monkeypatch, tmp_path, ["--alphas", "0.01", "--auc_alpha", "0.05"])
    with pytest.raises(SystemExit):
        _run_np(monkeypatch, tmp_path, ["--alphas", "1.5"])
