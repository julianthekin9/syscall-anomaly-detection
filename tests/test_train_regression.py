"""Mini-training regression: train_one_service on the FIXT dataset gives the same result as the code before the move.

The reference (golden.json -> "train", FIXT.pt) was produced by tests/golden/make_golden.py --train from the
old code with the same parameters (golden.json -> "train" -> "config") and seed.

At stage 3 the test was rewritten for args; the reference (golden.json, FIXT.pt) was NOT regenerated.
Reference parameters use old config names; OLD_CONFIG_TO_ARG maps them to arguments.
"""

import json
import random
from pathlib import Path

import numpy as np
import pytest
import torch
import yaml

from syscall_hids.tools import evaluation, resource_guard
from syscall_hids.tools import train as train_module
from syscall_hids.tools.arg_parser import build_default_arg_parser
from syscall_hids.tools.arg_parser_tools import check_args

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
FLOAT_TOL = 1e-5
OLD_CONFIG_TO_ARG = {
    "SERVICES": "services",
    "USE_ARG_COUNT_FEATURE": "use_arg_count_feature",
    "ARG_COUNT_BUCKETS": "arg_count_buckets",
    "FORCE_REBUILD_VOCAB": "force_rebuild_vocab",
    "EMBED_DIM_SYSCALL": "embed_dim_syscall",
    "EMBED_DIM_PROCESS": "embed_dim_process",
    "EMBED_DIM_DIRECTION": "embed_dim_direction",
    "EMBED_DIM_ARG_COUNT": "embed_dim_arg_count",
    "HIDDEN_DIM": "hidden_dim",
    "NUM_LAYERS": "num_layers",
    "DROPOUT": "dropout",
    "SEQ_LEN": "seq_len",
    "SEQ_STEP": "seq_step",
    "BATCH_SIZE": "batch_size",
    "LEARNING_RATE": "lr",
    "EPOCHS": "max_num_epochs",
    "RESUME": "restart_latest",
    "WINDOW_AGG": "window_agg",
    "WINDOW_AGG_QUANTILE": "window_agg_quantile",
    "THRESHOLD_PERCENTILE": "threshold_percentile",
    "EVAL_TEST_EVERY_EPOCH": "eval_test_every_epoch",
    "METRICS_EVAL_EVERY_N_EPOCHS": "metrics_eval_every_n_epochs",
    "TRAIN_METRICS_MAX_BATCHES": "train_metrics_max_batches",
    "RAM_GUARD_ENABLED": "ram_guard_enabled",
}


def _argv_from_golden_config(golden_config: dict) -> list[str]:
    argv: list[str] = []
    for key, value in golden_config.items():
        flag = f"--{OLD_CONFIG_TO_ARG[key]}"
        if isinstance(value, list):
            argv += [flag, *map(str, value)]
        else:
            argv += [flag, str(value)]  # True/False/None are parsed by str2bool and int_or_none
    return argv


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
        argv = _argv_from_golden_config(golden["config"])
        argv += ["--dataset_root", str(GOLDEN_DIR / "data"), "--work_dir", str(tmp)]
        args, _ = check_args(build_default_arg_parser().parse_args(argv))
        resource_guard.configure(
            args.ram_guard_enabled, args.ram_soft_limit_percent, args.ram_hard_limit_percent, args.ram_throttle_sleep_sec
        )
        mp.chdir(tmp)
        # Metrics are captured at the entry of the plotting functions, as in make_golden.py
        mp.setattr(train_module, "plot_training_curves", lambda service, h, plots_dir: history.update(h))
        mp.setattr(evaluation, "plot_roc_curve", lambda truth, scores, service, auc, tags, plots_dir: test_aucs.append(auc))

        random.seed(golden["seed"])
        np.random.seed(golden["seed"])
        torch.manual_seed(golden["seed"])
        torch.use_deterministic_algorithms(True)
        train_module.train_one_service("FIXT", torch.device("cpu"), args)
    finally:
        torch.use_deterministic_algorithms(deterministic)
        mp.undo()

    checkpoint = torch.load(Path(args.model_dir) / "FIXT.pt", map_location="cpu")
    return {"checkpoint": checkpoint, "history": history, "test_aucs": test_aucs, "args": args}


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


def test_reproducibility_artifacts(trained: dict) -> None:
    """train_args in the checkpoint and {model_dir}/FIXT_config.yaml, which parses back into the same args."""
    args = trained["args"]
    assert trained["checkpoint"]["train_args"] == vars(args)
    config_path = Path(args.model_dir) / "FIXT_config.yaml"
    assert yaml.safe_load(config_path.read_text(encoding="utf-8")) == {k: v for k, v in vars(args).items() if k != "config"}
    reparsed, _ = check_args(build_default_arg_parser().parse_args(["--config", str(config_path)]))
    assert {k: v for k, v in vars(reparsed).items() if k != "config"} == {k: v for k, v in vars(args).items() if k != "config"}
