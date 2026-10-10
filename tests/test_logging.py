"""Training logging: log and metrics files, sections, JSONL, setup_logger idempotency, plot from JSONL."""

import json
import logging
from pathlib import Path

import pytest

from syscall_hids.cli.run_train import run
from syscall_hids.tools.arg_parser import build_default_arg_parser
from syscall_hids.tools.utils import setup_logger
from syscall_hids.tools.visualization import plot_from_results

DATA_DIR = Path(__file__).resolve().parent / "golden" / "data"


@pytest.fixture(scope="module")
def work_dir(tmp_path_factory) -> Path:
    work = tmp_path_factory.mktemp("logging_run")
    args = build_default_arg_parser().parse_args([
        "--config", "configs/php_cwe_434.yaml",
        "--dataset_root", str(DATA_DIR), "--services", "FIXT",
        "--max_num_epochs", "1", "--hidden_dim", "16", "--work_dir", str(work),
    ])
    try:
        run(args)
    finally:
        setup_logger(directory=None)  # close file handlers so tmp can be cleaned up
    return work


def _records(work_dir: Path) -> list[dict]:
    path = work_dir / "results" / "hids_feat-syscall+process+direction+arg_count_FIXT_run-123_train.txt"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_files_exist(work_dir: Path) -> None:
    assert (work_dir / "logs" / "hids_feat-syscall+process+direction+arg_count_run-123.log").is_file()
    assert (work_dir / "logs" / "hids_feat-syscall+process+direction+arg_count_run-123_debug.log").is_file()
    assert (work_dir / "results" / "hids_feat-syscall+process+direction+arg_count_FIXT_run-123_train.txt").is_file()


def test_jsonl_parses_and_has_modes(work_dir: Path) -> None:
    modes = {r["mode"] for r in _records(work_dir)}
    assert {"opt", "eval", "threshold", "test", "ram"} <= modes


def test_log_sections(work_dir: Path) -> None:
    log = (work_dir / "logs" / "hids_feat-syscall+process+direction+arg_count_run-123.log").read_text(encoding="utf-8")
    for section in ("VERIFYING SETTINGS", "LOADING INPUT DATA", "MODEL DETAILS", "OPTIMIZER INFORMATION", "TRAINING", "RESULTS"):
        assert f"==========={section}===========" in log
    debug_log = (work_dir / "logs" / "hids_feat-syscall+process+direction+arg_count_run-123_debug.log").read_text(encoding="utf-8")
    assert "Configuration:" in debug_log
    assert "Current Git commit:" in debug_log


def test_plot_from_results(work_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "curves.png"
    assert plot_from_results(str(work_dir / "results" / "hids_feat-syscall+process+direction+arg_count_FIXT_run-123_train.txt"), str(out)) == str(out)
    assert out.stat().st_size > 0


def test_setup_logger_is_idempotent(tmp_path: Path) -> None:
    try:
        setup_logger(level="INFO", tag="dup", directory=str(tmp_path))
        setup_logger(level="INFO", tag="dup", directory=str(tmp_path))
        logging.info("one line")
    finally:
        setup_logger(directory=None)
    assert (tmp_path / "dup.log").read_text(encoding="utf-8").count("one line") == 1
