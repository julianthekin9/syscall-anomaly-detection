"""Логування, файл метрик, seed і git-коміт (за зразком mace/tools/utils.py)."""

import json
import logging
import os
import random
import subprocess
import sys

import numpy as np
import torch

# Позначка хендлерів, які додав setup_logger: їх знімаємо при повторному виклику,
# чужі (наприклад, pytest caplog) не чіпаємо
_HANDLER_MARK = "_syscall_hids_handler"


def get_tag(name: str, seed: int) -> str:
    return f"{name}_run-{seed}"


def setup_logger(
    level: int | str = logging.INFO,
    tag: str | None = None,
    directory: str | None = None,
    append: bool = False,
) -> None:
    """Кореневий логер: консоль і {directory}/{tag}.log на рівні level, {tag}_debug.log — усе з DEBUG.

    Ідемпотентна: повторний виклик (Colab/Jupyter) не дублює рядки.
    append=True дописує файли (продовження навчання), інакше вони перезаписуються.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    for handler in [h for h in logger.handlers if getattr(h, _HANDLER_MARK, False)]:
        logger.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    def add(handler: logging.Handler, handler_level: int | str) -> None:
        handler.setLevel(handler_level)
        handler.setFormatter(formatter)
        setattr(handler, _HANDLER_MARK, True)
        logger.addHandler(handler)

    add(logging.StreamHandler(stream=sys.stdout), level)
    if directory is not None and tag is not None:
        os.makedirs(directory, exist_ok=True)
        mode = "a" if append else "w"
        add(logging.FileHandler(os.path.join(directory, f"{tag}.log"), mode=mode, encoding="utf-8"), level)
        add(logging.FileHandler(os.path.join(directory, f"{tag}_debug.log"), mode=mode, encoding="utf-8"), logging.DEBUG)


class UniversalEncoder(json.JSONEncoder):
    """numpy / torch -> JSON."""

    def default(self, o):
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, torch.Tensor):
            return o.detach().cpu().numpy().tolist()
        return json.JSONEncoder.default(self, o)


class MetricsLogger:
    """JSONL: один рядок = один словник. Файл відкривається на кожен запис, тож дані на диску
    навіть якщо процес упав."""

    def __init__(self, directory: str, tag: str, append: bool = False) -> None:
        self.directory = directory
        self.path = os.path.join(directory, tag + ".txt")
        if not append:
            os.makedirs(self.directory, exist_ok=True)
            open(self.path, "w", encoding="utf-8").close()

    def log(self, d: dict) -> None:
        os.makedirs(self.directory, exist_ok=True)
        with open(self.path, mode="a", encoding="utf-8") as f:
            f.write(json.dumps(d, cls=UniversalEncoder))
            f.write("\n")


def set_seeds(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def get_git_commit() -> str:
    """Хеш поточного коміту репозиторію, з якого імпортовано пакет; "None", якщо git недоступний."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True, text=True, check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "None"
    return result.stdout.strip()
