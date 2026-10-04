"""Регресія міні-навчання: train_one_service на датасеті FIXT дає те саме, що код до переїзду.

Еталон (golden.json -> "train", FIXT.pt) знято tests/golden/make_golden.py --train зі
старого коду з тими самими параметрами (golden.json -> "train" -> "config") і seed.

На етапі 3 цей тест переписується під args, еталон (golden.json, FIXT.pt) НЕ перегенерується.
"""

import json
import random
from pathlib import Path

import numpy as np
import pytest
import torch

from syscall_hids import config
from syscall_hids.tools import evaluation
from syscall_hids.tools import train as train_module

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
FLOAT_TOL = 1e-5


def _close(actual: float | None, expected: float | None) -> bool:
    if expected is None:
        return actual is None
    return abs(actual - expected) <= FLOAT_TOL


@pytest.fixture(scope="module")
def golden() -> dict:
    return json.loads((GOLDEN_DIR / "golden.json").read_text(encoding="utf-8"))["train"]


@pytest.fixture(scope="module")
def trained(golden: dict, tmp_path_factory) -> dict:
    tmp = tmp_path_factory.mktemp("fixt_train")
    mp = pytest.MonkeyPatch()
    history: dict = {}
    test_aucs: list[float] = []
    deterministic = torch.are_deterministic_algorithms_enabled()
    try:
        for key, value in golden["config"].items():
            mp.setattr(config, key, value)
        mp.setattr(config, "DATASET_ROOT", str(GOLDEN_DIR / "data"))
        mp.setattr(config, "MODEL_DIR", str(tmp / "models"))
        mp.setattr(config, "CHECKPOINT_DIR", str(tmp / "models" / "checkpoints"))
        mp.setattr(config, "VOCAB_DIR", str(tmp / "vocabs"))
        mp.setattr(config, "PLOTS_DIR", str(tmp / "plots"))
        mp.chdir(tmp)
        # Метрики знімаються на вході функцій малювання, як і в make_golden.py
        mp.setattr(train_module, "plot_training_curves", lambda service, h: history.update(h))
        mp.setattr(evaluation, "plot_roc_curve", lambda truth, scores, service, auc, tags: test_aucs.append(auc))

        random.seed(golden["seed"])
        np.random.seed(golden["seed"])
        torch.manual_seed(golden["seed"])
        torch.use_deterministic_algorithms(True)
        train_module.train_one_service("FIXT", torch.device("cpu"))
    finally:
        torch.use_deterministic_algorithms(deterministic)
        mp.undo()

    checkpoint = torch.load(tmp / "models" / "FIXT.pt", map_location="cpu")
    return {"checkpoint": checkpoint, "history": history, "test_aucs": test_aucs}


def test_vocab_and_hparams_exact(golden: dict, trained: dict) -> None:
    ckpt = trained["checkpoint"]
    assert ckpt["vocabs"] == golden["vocabs"]
    assert ckpt["vocab_sizes"] == golden["vocab_sizes"]
    assert ckpt["hparams"] == golden["hparams"]
    assert ckpt["epochs_trained"] == golden["epochs_trained"]


def test_threshold(golden: dict, trained: dict) -> None:
    assert _close(trained["checkpoint"]["threshold"], golden["threshold"])


def test_history_per_epoch(golden: dict, trained: dict) -> None:
    assert trained["history"].keys() == golden["history"].keys()
    for key, expected in golden["history"].items():
        actual = trained["history"][key]
        assert len(actual) == len(expected), key
        assert all(_close(a, e) for a, e in zip(actual, expected)), f"{key}: {actual} != {expected}"


def test_test_auc_per_epoch(golden: dict, trained: dict) -> None:
    assert len(trained["test_aucs"]) == len(golden["test_auc_per_epoch"])
    assert all(_close(a, e) for a, e in zip(trained["test_aucs"], golden["test_auc_per_epoch"]))


def test_state_dict_sum_and_norm(golden: dict, trained: dict) -> None:
    state = trained["checkpoint"]["model_state"]
    assert sorted(state) == sorted(golden["state_dict"])
    for name, (exp_sum, exp_norm) in golden["state_dict"].items():
        tensor = state[name].double()
        assert _close(tensor.sum().item(), exp_sum), f"{name}: sum"
        assert _close(tensor.norm().item(), exp_norm), f"{name}: norm"
