"""hids-eval --eval-test-split на фікстурах tests/golden: відпрацьовує без винятку, AUC = еталонний."""

import json
import shutil
import sys
from pathlib import Path

import torch

from syscall_hids import config
from syscall_hids.cli import eval_recordings
from syscall_hids.tools import evaluation

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"


def test_eval_test_split_matches_golden_auc(tmp_path: Path, monkeypatch) -> None:
    # Розкладка, якої чекає build_test_sequences: <root>/<сервіс>/test/{normal,abnormal}
    for group in ("normal", "abnormal"):
        shutil.copytree(GOLDEN_DIR / "data" / group, tmp_path / "FLASK" / "test" / group)
    shutil.copy(GOLDEN_DIR / "FLASK.pt", tmp_path / "FLASK.pt")

    monkeypatch.setattr(config, "DATASET_ROOT", str(tmp_path))
    monkeypatch.setattr(config, "MODEL_DIR", str(tmp_path))
    monkeypatch.setattr(config, "PLOTS_DIR", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)  # еталон рахувався на CPU

    reported: list[float] = []
    monkeypatch.setattr(evaluation, "plot_roc_curve", lambda truth, scores, service, auc, tags: reported.append(auc))
    monkeypatch.setattr(sys, "argv", ["hids-eval", "--service", "FLASK", "--eval-test-split"])

    eval_recordings.main()

    golden = json.loads((GOLDEN_DIR / "golden.json").read_text(encoding="utf-8"))
    assert len(reported) == 1, "ROC-AUC не порахований"
    assert abs(reported[0] - golden["auc"]) <= 1e-6
