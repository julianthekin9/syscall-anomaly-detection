from pathlib import Path
from typing import Literal

from syscall_hids import config

Split = Literal["train", "val", "test"]

_SPLIT_SUBDIR = {
    "train": config.TRAIN_SUBDIR,
    "val": config.VAL_SUBDIR,
    "test": config.TEST_SUBDIR,
}


def _root_is_single_service() -> bool:
    root = Path(config.DATASET_ROOT)
    return (root / config.TRAIN_SUBDIR).is_dir() and (root / config.TEST_SUBDIR).is_dir()


def list_services() -> list[str]:
    root = Path(config.DATASET_ROOT)
    if not root.exists():
        raise FileNotFoundError(f"Не найдена DATASET_ROOT={root} — проверьте config.DATASET_ROOT.")

    if _root_is_single_service():
        names = [root.name]
    else:
        names = sorted(p.name for p in root.iterdir() if p.is_dir())

    if config.SERVICES is not None:
        names = [n for n in names if n in config.SERVICES]
    return names


def _split_dir(service_name: str, split: Split) -> Path:
    root = Path(config.DATASET_ROOT)
    if _root_is_single_service() and service_name == root.name:
        return root / _SPLIT_SUBDIR[split]
    return root / service_name / _SPLIT_SUBDIR[split]


def recording_files(service_name: str, split: Split) -> list[Path]:
    split_dir = _split_dir(service_name, split)
    if not split_dir.exists():
        raise FileNotFoundError(
            f"Не найдена папка сплита {split_dir} — проверьте config.{split.upper()}_SUBDIR "
            f"на соответствие реальной структуре датасета (ожидается либо "
            f"DATASET_ROOT/<сценарий>/<{split}-подпапка>, либо, если DATASET_ROOT "
            f"уже указывает на папку одного сценария, DATASET_ROOT/<{split}-подпапка>)."
        )
    return sorted(split_dir.rglob(f"*{config.RECORDING_EXTENSION}"))


def test_recording_files(service_name: str) -> tuple[list[Path], list[Path]]:

    test_dir = _split_dir(service_name, "test")
    normal_dir = test_dir / config.TEST_NORMAL_SUBDIR
    abnormal_dir = test_dir / config.TEST_ABNORMAL_SUBDIR

    if not normal_dir.is_dir() or not abnormal_dir.is_dir():
        raise FileNotFoundError(
            f"Expected subdirs {normal_dir}, {abnormal_dir}."
        )
    normal_files = sorted(normal_dir.rglob(f"*{config.RECORDING_EXTENSION}"))
    abnormal_files = sorted(abnormal_dir.rglob(f"*{config.RECORDING_EXTENSION}"))

    return normal_files, abnormal_files
