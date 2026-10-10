"""Підмножина ознак: модель будує ембединги лише для вибраних, а hids-eval скорить її за ознаками з чекпоінта."""

import sys
from pathlib import Path

import pytest
import torch

from syscall_hids.cli import eval_recordings
from syscall_hids.cli.eval_recordings import score_log_file
from syscall_hids.tools import evaluation, resource_guard
from syscall_hids.tools.arg_parser import build_default_arg_parser
from syscall_hids.tools.arg_parser_tools import check_args
from syscall_hids.tools.checkpoint import load_model
from syscall_hids.tools.train import train_one_service

DATA_DIR = Path(__file__).resolve().parent / "golden" / "data"


@pytest.fixture(scope="module")
def trained(tmp_path_factory) -> tuple[Path, object]:
    work = tmp_path_factory.mktemp("features_run")
    args, _ = check_args(build_default_arg_parser().parse_args([
        "--dataset_root", str(DATA_DIR), "--services", "FIXT", "--features", "direction,syscall",
        "--max_num_epochs", "1", "--hidden_dim", "16", "--ram_guard_enabled", "false", "--work_dir", str(work),
    ]))
    resource_guard.configure(
        args.ram_guard_enabled, args.ram_soft_limit_percent, args.ram_hard_limit_percent, args.ram_throttle_sleep_sec
    )
    train_one_service("FIXT", torch.device("cpu"), args)
    return work, args


def test_model_uses_only_selected_features(trained) -> None:
    _, args = trained
    model, checkpoint = load_model("FIXT", torch.device("cpu"), args.model_dir)
    assert list(checkpoint["hparams"]["features"]) == ["syscall", "direction"]
    assert list(model.embeddings) == ["syscall", "direction"]
    assert model.lstm.input_size == args.embed_dim_syscall + args.embed_dim_direction
    assert "arg_count" not in checkpoint["vocab_sizes"]


def test_results_file_has_features_tag(trained) -> None:
    _, args = trained
    assert (Path(args.results_dir) / "hids_feat-syscall+direction_FIXT_run-123_train.txt").is_file()


def test_score_log_file(trained) -> None:
    _, args = trained
    model, checkpoint = load_model("FIXT", torch.device("cpu"), args.model_dir)
    scores = score_log_file(model, checkpoint, str(DATA_DIR / "FIXT" / "test" / "abnormal" / sorted(
        p.name for p in (DATA_DIR / "FIXT" / "test" / "abnormal").iterdir())[0]), torch.device("cpu"), 32)
    assert scores and all(s == s for s in scores)


def test_eval_test_split(trained, monkeypatch) -> None:
    work, args = trained
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    reported: list[float] = []
    monkeypatch.setattr(evaluation, "plot_roc_curve", lambda truth, scores, service, auc, tags, plots_dir: reported.append(auc))
    monkeypatch.setattr(sys, "argv", [
        "hids-eval", "--service", "FIXT", "--eval-test-split",
        "--dataset_root", str(DATA_DIR), "--model_dir", args.model_dir, "--plots_dir", str(work),
        "--ram_guard_enabled", "false",
    ])
    eval_recordings.main()
    assert len(reported) == 1
