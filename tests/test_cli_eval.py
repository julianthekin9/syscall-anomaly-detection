"""hids-eval --eval-test-split on the tests/golden fixtures: runs without exceptions, AUC = reference."""

import json
import shutil
import sys
from pathlib import Path

import torch

from syscall_hids.cli import eval_recordings
from syscall_hids.tools import evaluation

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"


def test_eval_test_split_matches_golden_auc(tmp_path: Path, monkeypatch) -> None:
    # Layout expected by build_test_sequences: <root>/<service>/test/{normal,abnormal}
    for group in ("normal", "abnormal"):
        shutil.copytree(GOLDEN_DIR / "data" / group, tmp_path / "FLASK" / "test" / group)
    shutil.copy(GOLDEN_DIR / "FLASK.pt", tmp_path / "FLASK.pt")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)  # the reference was computed on CPU

    reported: list[float] = []
    monkeypatch.setattr(evaluation, "plot_roc_curve", lambda truth, scores, service, auc, tags, plots_dir: reported.append(auc))
    monkeypatch.setattr(sys, "argv", [
        "hids-eval", "--service", "FLASK", "--eval-test-split",
        "--dataset_root", str(tmp_path), "--model_dir", str(tmp_path), "--plots_dir", str(tmp_path),
    ])

    eval_recordings.main()

    golden = json.loads((GOLDEN_DIR / "golden.json").read_text(encoding="utf-8"))
    assert len(reported) == 1, "ROC-AUC was not computed"
    assert abs(reported[0] - golden["auc"]) <= 1e-6
