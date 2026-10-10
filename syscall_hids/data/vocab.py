import json
from pathlib import Path

import numpy as np

from syscall_hids.data.layout import recording_files
from syscall_hids.data.parsing import read_recording

PAD = "<PAD>"
UNK = "<UNK>"
# Канонічний порядок вхідних ознак: у ньому кодуються колонки та конкатенуються ембединги.
# syscall завжди перший (колонка 0 — ціль передбачення)
FEATURE_NAMES = ["syscall", "process", "direction", "arg_count"]
VOCAB_FEATURE_NAMES = ["syscall", "process", "direction"]  # ознаки зі словником (arg_count — бакети)


def vocab_path(service_name: str, vocab_dir: str) -> Path:
    """Path to the cached vocab of a service (vocab_dir/<service>.json)."""
    return Path(vocab_dir) / f"{service_name}.json"


def save_vocab(service_name: str, vocabs: dict[str, dict[str, int]], vocab_dir: str) -> None:
    path = vocab_path(service_name, vocab_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(vocabs, f, ensure_ascii=False, indent=2)


def load_vocab(service_name: str, vocab_dir: str) -> dict[str, dict[str, int]] | None:
    """Reads the cached vocab from disk. None if there is no cache yet."""
    path = vocab_path(service_name, vocab_dir)
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


_SEQ_DTYPE = np.int16  # see _check_vocab_fits_dtype below for why int16


def _check_vocab_fits_dtype(vocabs: dict[str, dict[str, int]]) -> None:
    limit = np.iinfo(_SEQ_DTYPE).max
    too_big = {name: len(v) for name, v in vocabs.items() if len(v) > limit}
    if too_big:
        raise ValueError(
            f"Vocabs {too_big} exceed the capacity of {_SEQ_DTYPE.__name__} (max {limit}): "
            f"change data._SEQ_DTYPE to np.int32 manually if your vocabs are that large."
        )


def build_vocab(
    service_name: str, dataset_root: str, vocab_dir: str, use_cache: bool = True
) -> dict[str, dict[str, int]]:

    if use_cache:
        cached = load_vocab(service_name, vocab_dir)
        if cached is not None:
            _check_vocab_fits_dtype(cached)
            return cached

    raw_values: dict[str, set] = {name: set() for name in VOCAB_FEATURE_NAMES}
    for rec_path in recording_files(service_name, "train", dataset_root):
        for line in read_recording(str(rec_path)):
            raw_values["syscall"].add(line.syscall)
            raw_values["process"].add(line.process_name)
            raw_values["direction"].add(line.direction)

    vocabs: dict[str, dict[str, int]] = {}
    for name in VOCAB_FEATURE_NAMES:
        sorted_values = sorted(raw_values[name])
        vocab = {PAD: 0, UNK: 1}
        vocab.update({value: i + 2 for i, value in enumerate(sorted_values)})
        vocabs[name] = vocab

    _check_vocab_fits_dtype(vocabs)
    save_vocab(service_name, vocabs, vocab_dir)
    return vocabs
