"""Argument parsing: defaults, YAML, priority CLI > YAML > defaults, check_args."""

import os
from pathlib import Path

import pytest

from syscall_hids.tools.arg_parser import build_default_arg_parser, build_eval_arg_parser
from syscall_hids.tools.arg_parser_tools import check_args

# The former syscall_hids/config.yaml (keys already renamed to argument names)
EXPECTED_DEFAULTS = {
    "dataset_root": "./DATASET_LIDDS",
    "services": ["PHP_CWE-434"],
    "features": ["syscall", "process", "direction", "arg_count"],
    "arg_count_buckets": 8,
    "force_rebuild_vocab": False,
    "embed_dim_syscall": 16,
    "embed_dim_process": 8,
    "embed_dim_direction": 2,
    "embed_dim_arg_count": 4,
    "hidden_dim": 200,
    "num_layers": 2,
    "dropout": 0.2,
    "seq_len": 64,
    "seq_step": 32,
    "batch_size": 32,
    "lr": 1e-4,
    "max_num_epochs": 100,
    "restart_latest": False,
    "window_agg": "quantile",
    "window_agg_quantile": 0.90,
    "threshold_percentile": 99.0,
    "eval_test_every_epoch": True,
    "metrics_eval_every_n_epochs": 1,
    "train_metrics_max_batches": None,
    "work_dir": ".",
    "model_dir": None,
    "checkpoints_dir": None,
    "plots_dir": None,
    "vocab_dir": None,
    "ram_guard_enabled": True,
    "ram_soft_limit_percent": 80.0,
    "ram_hard_limit_percent": 92.0,
    "ram_throttle_sleep_sec": 2.0,
    "ram_check_every_n_recordings": 20,
    "name": "hids",
    "seed": 123,
    "log_level": "INFO",
    "log_dir": None,
    "results_dir": None,
}


def _yaml(tmp_path: Path, text: str) -> str:
    path = tmp_path / "cfg.yaml"
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_defaults_without_config() -> None:
    args = build_default_arg_parser().parse_args([])
    actual = {k: v for k, v in vars(args).items() if k != "config"}
    assert actual == EXPECTED_DEFAULTS


def test_yaml_overrides_default(tmp_path: Path) -> None:
    args = build_default_arg_parser().parse_args(["--config", _yaml(tmp_path, "hidden_dim: 64\nservices: [A, B]\n")])
    assert args.hidden_dim == 64
    assert args.services == ["A", "B"]
    assert args.lr == EXPECTED_DEFAULTS["lr"]


def test_cli_overrides_yaml(tmp_path: Path) -> None:
    cfg = _yaml(tmp_path, "lr: 1.0e-3\nmax_num_epochs: 7\n")
    args = build_default_arg_parser().parse_args(["--config", cfg, "--lr", "5e-4"])
    assert args.lr == 5e-4
    assert args.max_num_epochs == 7


def test_yaml_false_bool(tmp_path: Path) -> None:
    args = build_default_arg_parser().parse_args(["--config", _yaml(tmp_path, "force_rebuild_vocab: false\n")])
    assert args.force_rebuild_vocab is False


@pytest.mark.parametrize("argv", [["--features", "process,syscall"], ["--features", "process", "syscall"]])
def test_features_cli_canonical_order(argv) -> None:
    args, _ = check_args(build_default_arg_parser().parse_args(argv))
    assert args.features == ["syscall", "process"]


def test_features_cli_overrides_yaml(tmp_path: Path) -> None:
    cfg = _yaml(tmp_path, "features: [syscall, direction]\n")
    args, _ = check_args(build_default_arg_parser().parse_args(["--config", cfg]))
    assert args.features == ["syscall", "direction"]
    args, _ = check_args(build_default_arg_parser().parse_args(["--config", cfg, "--features", "syscall,arg_count"]))
    assert args.features == ["syscall", "arg_count"]


@pytest.mark.parametrize("features", ["process,direction", "syscall,pid", "syscall,process,syscall"])
def test_features_invalid(features: str) -> None:
    with pytest.raises(ValueError):
        check_args(build_default_arg_parser().parse_args(["--features", features]))


def test_unknown_yaml_key_is_error_for_train(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        build_default_arg_parser().parse_args(["--config", _yaml(tmp_path, "hiden_dim: 64\n")])


def test_eval_parser_ignores_train_keys() -> None:
    args = build_eval_arg_parser().parse_args(["--config", "configs/php_cwe_434.yaml", "--service", "PHP_CWE-434"])
    assert args.dataset_root == "./DATASET_LIDDS"
    assert not hasattr(args, "hidden_dim")


def test_check_args_derives_paths_from_work_dir() -> None:
    args, _ = check_args(build_default_arg_parser().parse_args(["--work_dir", "runs/x"]))
    assert args.model_dir == os.path.join("runs/x", "models")
    assert args.checkpoints_dir == os.path.join("runs/x", "models", "checkpoints")
    assert args.plots_dir == os.path.join("runs/x", "training_plots")
    assert args.vocab_dir == os.path.join("runs/x", "vocabs")
    assert args.log_dir == os.path.join("runs/x", "logs")
    assert args.results_dir == os.path.join("runs/x", "results")


def test_check_args_rejects_bad_seq_step() -> None:
    with pytest.raises(ValueError):
        check_args(build_default_arg_parser().parse_args(["--seq_step", "128"]))


def test_check_args_warnings() -> None:
    _, messages = check_args(build_default_arg_parser().parse_args(
        ["--window_agg", "max", "--window_agg_quantile", "0.5", "--features", "syscall,process,direction"]
    ))
    assert len(messages) == 2
