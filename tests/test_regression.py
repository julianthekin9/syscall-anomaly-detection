"""Регресія: оконні скори та AUC поточного коду збігаються з кодом до переїзду в пакет.

Еталон (tests/golden/golden.json) згенеровано tests/golden/make_golden.py зі старого коду.
"""

import json
from pathlib import Path

import pytest
import torch
from sklearn.metrics import roc_auc_score

from syscall_hids.cli.eval_recordings import score_log_file
from syscall_hids.modules.models import SyscallLSTM

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
TOL = 1e-6


@pytest.fixture(scope="module")
def golden() -> dict:
    return json.loads((GOLDEN_DIR / "golden.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def current_scores(golden: dict) -> dict[str, list[float]]:
    device = torch.device("cpu")
    checkpoint = torch.load(GOLDEN_DIR / "FLASK.pt", map_location=device)
    model = SyscallLSTM.from_checkpoint(checkpoint, device)
    model.eval()
    return {
        name: score_log_file(model, checkpoint, str(GOLDEN_DIR / "data" / name), device)
        for name in golden["scores"]
    }


def test_window_scores_match(golden: dict, current_scores: dict[str, list[float]]) -> None:
    for name, expected in golden["scores"].items():
        actual = current_scores[name]
        assert len(actual) == len(expected), f"{name}: кількість вікон {len(actual)} != {len(expected)}"
        worst = max(abs(a - e) for a, e in zip(actual, expected))
        assert worst <= TOL, f"{name}: максимальне відхилення скору {worst:.3e} > {TOL}"


def test_auc_matches(golden: dict, current_scores: dict[str, list[float]]) -> None:
    truth: list[bool] = []
    flat: list[float] = []
    for name, scores in current_scores.items():
        truth += [name.startswith("abnormal/")] * len(scores)
        flat += scores
    assert abs(roc_auc_score(truth, flat) - golden["auc"]) <= TOL
