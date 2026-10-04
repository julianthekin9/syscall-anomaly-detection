import json
from pathlib import Path

import numpy as np

from syscall_hids import config
from syscall_hids.data.layout import recording_files
from syscall_hids.data.parsing import read_recording

PAD = "<PAD>"
UNK = "<UNK>"
FEATURE_NAMES = ["syscall", "process", "direction"]  # + "arg_count", если config.USE_ARG_COUNT_FEATURE


def vocab_path(service_name: str) -> Path:
    """Путь к закэшированному словарю сервиса (config.VOCAB_DIR/<сервис>.json)."""
    return Path(config.VOCAB_DIR) / f"{service_name}.json"


def save_vocab(service_name: str, vocabs: dict[str, dict[str, int]]) -> None:
    path = vocab_path(service_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(vocabs, f, ensure_ascii=False, indent=2)


def load_vocab(service_name: str) -> dict[str, dict[str, int]] | None:
    """Читает закэшированный словарь с диска. None, если кэша ещё нет."""
    path = vocab_path(service_name)
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


_SEQ_DTYPE = np.int16  # см. _check_vocab_fits_dtype ниже — почему именно int16


def _check_vocab_fits_dtype(vocabs: dict[str, dict[str, int]]) -> None:
    limit = np.iinfo(_SEQ_DTYPE).max
    too_big = {name: len(v) for name, v in vocabs.items() if len(v) > limit}
    if too_big:
        raise ValueError(
            f"Словари {too_big} превышают ёмкость {_SEQ_DTYPE.__name__} (макс {limit}) — "
            f"поменяйте data._SEQ_DTYPE на np.int32 вручную, если у вас настолько большие словари."
        )


def build_vocab(service_name: str, use_cache: bool = True) -> dict[str, dict[str, int]]:

    if use_cache:
        cached = load_vocab(service_name)
        if cached is not None:
            _check_vocab_fits_dtype(cached)
            return cached

    raw_values: dict[str, set] = {name: set() for name in FEATURE_NAMES}
    for rec_path in recording_files(service_name, "train"):
        for line in read_recording(str(rec_path)):
            raw_values["syscall"].add(line.syscall)
            raw_values["process"].add(line.process_name)
            raw_values["direction"].add(line.direction)

    vocabs: dict[str, dict[str, int]] = {}
    for name in FEATURE_NAMES:
        sorted_values = sorted(raw_values[name])
        vocab = {PAD: 0, UNK: 1}
        vocab.update({value: i + 2 for i, value in enumerate(sorted_values)})
        vocabs[name] = vocab

    _check_vocab_fits_dtype(vocabs)
    save_vocab(service_name, vocabs)
    return vocabs
