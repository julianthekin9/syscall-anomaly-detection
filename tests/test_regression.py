"""Регресія інференсу: оконні скори та AUC поточного коду збігаються з кодом до переїзду в пакет.

Еталон (tests/golden/golden.json) згенеровано tests/golden/make_golden.py зі старого коду.
Два випадки:
- FLASK.pt: справжній старий чекпоінт завантажується і дає ті самі скори. Його словник
  майже не покриває фікстури (процес завжди UNK), тож кодування він майже не перевіряє;
- FIXT.pt: чекпоінт міні-навчання, словник якого збудовано на тих самих даних.
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
# випадок -> (чекпоінт, тека з normal/ і abnormal/, ключ еталону в golden.json; None — корінь)
CASES = {
    "FLASK": ("FLASK.pt", GOLDEN_DIR / "data", None),
    "FIXT": ("FIXT.pt", GOLDEN_DIR / "data" / "FIXT" / "test", "fixt_inference"),
}


@pytest.fixture(scope="module", params=list(CASES))
def case(request) -> tuple[dict, dict[str, list[float]]]:
    """(еталон із ключами auc/scores, поточні скори) для одного чекпоінта."""
    ckpt_name, data_dir, key = CASES[request.param]
    golden = json.loads((GOLDEN_DIR / "golden.json").read_text(encoding="utf-8"))
    golden = golden if key is None else golden[key]

    device = torch.device("cpu")
    checkpoint = torch.load(GOLDEN_DIR / ckpt_name, map_location=device)
    model = SyscallLSTM.from_checkpoint(checkpoint, device)
    model.eval()
    # batch_size=32 — колишній config.BATCH_SIZE, з яким знято еталон
    current = {name: score_log_file(model, checkpoint, str(data_dir / name), device, 32) for name in golden["scores"]}
    return golden, current


def test_window_scores_match(case) -> None:
    golden, current_scores = case
    for name, expected in golden["scores"].items():
        actual = current_scores[name]
        assert len(actual) == len(expected), f"{name}: кількість вікон {len(actual)} != {len(expected)}"
        worst = max(abs(a - e) for a, e in zip(actual, expected))
        assert worst <= TOL, f"{name}: максимальне відхилення скору {worst:.3e} > {TOL}"


def test_auc_matches(case) -> None:
    golden, current_scores = case
    truth: list[bool] = []
    flat: list[float] = []
    for name, scores in current_scores.items():
        truth += [name.startswith("abnormal/")] * len(scores)
        flat += scores
    assert abs(roc_auc_score(truth, flat) - golden["auc"]) <= TOL
