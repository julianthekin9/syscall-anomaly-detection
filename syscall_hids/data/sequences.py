from collections.abc import Sequence
from pathlib import Path

import numpy as np

from syscall_hids.data.layout import Split, recording_files, test_recording_files
from syscall_hids.data.parsing import ParsedLine, read_recording
from syscall_hids.data.vocab import UNK, _SEQ_DTYPE
from syscall_hids.tools import resource_guard

# Поле ParsedLine для ознак зі словником
_LINE_ATTR = {"syscall": "syscall", "process": "process_name", "direction": "direction"}


def encode_line(
    vocabs: dict[str, dict[str, int]], line: ParsedLine, features: Sequence[str], arg_count_buckets: int
) -> list[int]:
    """Індекси вибраних ознак у порядку features (канонічному, syscall першим)."""
    row = []
    for name in features:
        if name == "arg_count":
            row.append(min(line.arg_count, arg_count_buckets - 1))
        else:
            vocab = vocabs[name]
            row.append(vocab.get(getattr(line, _LINE_ATTR[name]), vocab[UNK]))
    return row


def encode_recording(
    vocabs: dict[str, dict[str, int]], lines: list[ParsedLine], features: Sequence[str], arg_count_buckets: int
) -> np.ndarray:
    arr = np.empty((len(lines), len(features)), dtype=_SEQ_DTYPE)
    for i, line in enumerate(lines):
        arr[i, :] = encode_line(vocabs, line, features, arg_count_buckets)
    return arr


def make_sequences(rows: np.ndarray, seq_len: int, step: int) -> tuple[np.ndarray, np.ndarray]:
    n_feat = rows.shape[1]
    n = len(rows)
    needed = seq_len + 1
    if n < needed:
        return np.empty((0, seq_len, n_feat), dtype=_SEQ_DTYPE), np.empty((0, seq_len, 1), dtype=_SEQ_DTYPE)

    starts = list(range(0, n - needed + 1, step))
    last_start = starts[-1] if starts else 0
    if last_start + needed < n:
        starts.append(n - needed)  # align the last window to the end so the tail is not lost

    n_windows = len(starts)
    X = np.empty((n_windows, seq_len, n_feat), dtype=_SEQ_DTYPE)
    # the last dimension is kept (=1) rather than removed, so that
    # model.compute_step_scores(targets[..., 0]) does not need changes
    y = np.empty((n_windows, seq_len, 1), dtype=_SEQ_DTYPE)
    for i, start in enumerate(starts):
        chunk = rows[start : start + needed]
        X[i] = chunk[:-1]
        y[i, :, 0] = chunk[1:, 0]  # next syscall is the only target after removing the process head
    return X, y


def build_normal_sequences(
    service_name: str,
    vocabs: dict[str, dict[str, int]],
    split: Split,
    seq_len: int,
    step: int,
    dataset_root: str,
    features: Sequence[str],
    arg_count_buckets: int,
    ram_check_every_n_recordings: int,
) -> tuple[np.ndarray, np.ndarray]:

    X_parts: list[np.ndarray] = []
    y_parts: list[np.ndarray] = []
    for i, rec_path in enumerate(recording_files(service_name, split, dataset_root)):
        lines = read_recording(str(rec_path))
        if len(lines) < seq_len + 1:
            continue
        rows = encode_recording(vocabs, lines, features, arg_count_buckets)
        X, y = make_sequences(rows, seq_len, step)
        if len(X):
            X_parts.append(X)
            y_parts.append(y)
        if (i + 1) % ram_check_every_n_recordings == 0:
            resource_guard.check_ram(f"{service_name}/{split}: after {i + 1} recordings")

    if not X_parts:
        return np.empty((0, seq_len, len(features)), dtype=_SEQ_DTYPE), np.empty((0, seq_len, 1), dtype=_SEQ_DTYPE)

    resource_guard.check_ram(f"{service_name}/{split}: before concatenation ({len(X_parts)} recordings)")
    X_all = np.concatenate(X_parts, axis=0)
    y_all = np.concatenate(y_parts, axis=0)
    resource_guard.check_ram(f"{service_name}/{split}: after concatenation ({len(X_all)} windows)")
    return X_all, y_all


def build_test_sequences(
    service_name: str,
    vocabs: dict[str, dict[str, int]],
    seq_len: int,
    step: int,
    dataset_root: str,
    features: Sequence[str],
    arg_count_buckets: int,
    ram_check_every_n_recordings: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    
    normal_files, abnormal_files = test_recording_files(service_name, dataset_root)

    X_parts: list[np.ndarray] = []
    y_parts: list[np.ndarray] = []
    attack_parts: list[np.ndarray] = []

    def process_group(files: list[Path], is_attack: bool) -> None:
        for i, rec_path in enumerate(files):
            lines = read_recording(str(rec_path))
            if len(lines) < seq_len + 1:
                continue
            rows = encode_recording(vocabs, lines, features, arg_count_buckets)
            X, y = make_sequences(rows, seq_len, step)
            if not len(X):
                continue
            X_parts.append(X)
            y_parts.append(y)
            attack_parts.append(np.full(len(X), is_attack, dtype=bool))
            if (i + 1) % ram_check_every_n_recordings == 0:
                group = "abnormal" if is_attack else "normal"
                resource_guard.check_ram(f"{service_name}/test/{group}: after {i + 1} recordings")

    process_group(normal_files, False)
    process_group(abnormal_files, True)

    if not X_parts:
        return (
            np.empty((0, seq_len, len(features)), dtype=_SEQ_DTYPE),
            np.empty((0, seq_len, 1), dtype=_SEQ_DTYPE),
            np.empty((0,), dtype=bool),
        )

    resource_guard.check_ram(f"{service_name}/test: before concatenation ({len(X_parts)} recordings)")
    X_all = np.concatenate(X_parts, axis=0)
    y_all = np.concatenate(y_parts, axis=0)
    attack_all = np.concatenate(attack_parts, axis=0)
    resource_guard.check_ram(f"{service_name}/test: after concatenation ({len(X_all)} windows, "
                              f"{attack_all.sum()} attack / {len(attack_all)} total)")
    return X_all, y_all, attack_all
