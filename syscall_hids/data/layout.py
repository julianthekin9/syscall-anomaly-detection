from pathlib import Path
from typing import Literal

from syscall_hids.data.format import RECORDING_EXTENSION

# Dataset layout (not experiment parameters)
TRAIN_SUBDIR = "training"
VAL_SUBDIR = "validation"
TEST_SUBDIR = "test"

TEST_NORMAL_SUBDIR = "normal"
TEST_ABNORMAL_SUBDIR = "abnormal"

Split = Literal["train", "val", "test"]

_SPLIT_SUBDIR = {
    "train": TRAIN_SUBDIR,
    "val": VAL_SUBDIR,
    "test": TEST_SUBDIR,
}


def _root_is_single_service(dataset_root: str) -> bool:
    root = Path(dataset_root)
    return (root / TRAIN_SUBDIR).is_dir() and (root / TEST_SUBDIR).is_dir()


def list_services(dataset_root: str, services: list[str] | None) -> list[str]:
    root = Path(dataset_root)
    if not root.exists():
        raise FileNotFoundError(f"dataset_root={root} not found, check --dataset_root.")

    if _root_is_single_service(dataset_root):
        names = [root.name]
    else:
        names = sorted(p.name for p in root.iterdir() if p.is_dir())

    if services is not None:
        names = [n for n in names if n in services]
    return names


def _split_dir(service_name: str, split: Split, dataset_root: str) -> Path:
    root = Path(dataset_root)
    if _root_is_single_service(dataset_root) and service_name == root.name:
        return root / _SPLIT_SUBDIR[split]
    return root / service_name / _SPLIT_SUBDIR[split]


def recording_files(service_name: str, split: Split, dataset_root: str) -> list[Path]:
    split_dir = _split_dir(service_name, split, dataset_root)
    if not split_dir.exists():
        raise FileNotFoundError(
            f"Split directory {split_dir} not found, check that {split.upper()}_SUBDIR "
            f"matches the actual dataset structure (expected either "
            f"dataset_root/<scenario>/<{split}-subdir>, or, if dataset_root "
            f"already points to a single scenario directory, dataset_root/<{split}-subdir>)."
        )
    return sorted(split_dir.rglob(f"*{RECORDING_EXTENSION}"))


def test_recording_files(service_name: str, dataset_root: str) -> tuple[list[Path], list[Path]]:

    test_dir = _split_dir(service_name, "test", dataset_root)
    normal_dir = test_dir / TEST_NORMAL_SUBDIR
    abnormal_dir = test_dir / TEST_ABNORMAL_SUBDIR

    if not normal_dir.is_dir() or not abnormal_dir.is_dir():
        raise FileNotFoundError(
            f"Expected subdirs {normal_dir}, {abnormal_dir}."
        )
    normal_files = sorted(normal_dir.rglob(f"*{RECORDING_EXTENSION}"))
    abnormal_files = sorted(abnormal_dir.rglob(f"*{RECORDING_EXTENSION}"))

    return normal_files, abnormal_files
