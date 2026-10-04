from pathlib import Path

import numpy as np

from syscall_hids import config
from syscall_hids.data.layout import Split, recording_files, test_recording_files
from syscall_hids.data.parsing import ParsedLine, read_recording
from syscall_hids.data.vocab import FEATURE_NAMES, UNK, _SEQ_DTYPE
from syscall_hids.tools import resource_guard

def encode_line(vocabs: dict[str, dict[str, int]], line: ParsedLine) -> list[int]:
    """[syscall_idx, process_idx, direction_idx, (arg_count_bucket)]."""
    row = [
        vocabs["syscall"].get(line.syscall, vocabs["syscall"][UNK]),
        vocabs["process"].get(line.process_name, vocabs["process"][UNK]),
        vocabs["direction"].get(line.direction, vocabs["direction"][UNK]),
    ]
    if config.USE_ARG_COUNT_FEATURE:
        row.append(min(line.arg_count, config.ARG_COUNT_BUCKETS - 1))
    return row


def num_features() -> int:
    return len(FEATURE_NAMES) + (1 if config.USE_ARG_COUNT_FEATURE else 0)


def encode_recording(vocabs: dict[str, dict[str, int]], lines: list[ParsedLine]) -> np.ndarray:
    arr = np.empty((len(lines), num_features()), dtype=_SEQ_DTYPE)
    for i, line in enumerate(lines):
        arr[i, :] = encode_line(vocabs, line)
    return arr


def make_sequences(rows: np.ndarray, seq_len: int, step: int) -> tuple[np.ndarray, np.ndarray]:
    n_feat = rows.shape[1] if rows.ndim == 2 else num_features()
    n = len(rows)
    needed = seq_len + 1
    if n < needed:
        return np.empty((0, seq_len, n_feat), dtype=_SEQ_DTYPE), np.empty((0, seq_len, 1), dtype=_SEQ_DTYPE)

    starts = list(range(0, n - needed + 1, step))
    last_start = starts[-1] if starts else 0
    if last_start + needed < n:
        starts.append(n - needed)  # прижимаем последнее окно к концу, не теряя хвост

    n_windows = len(starts)
    X = np.empty((n_windows, seq_len, n_feat), dtype=_SEQ_DTYPE)
    # последняя размерность оставлена (=1), а не убрана совсем, чтобы
    # model.compute_step_scores(targets[..., 0]) не пришлось менять
    y = np.empty((n_windows, seq_len, 1), dtype=_SEQ_DTYPE)
    for i, start in enumerate(starts):
        chunk = rows[start : start + needed]
        X[i] = chunk[:-1]
        y[i, :, 0] = chunk[1:, 0]  # next syscall — единственная цель после удаления process-головы
    return X, y


def build_normal_sequences(
    service_name: str, vocabs: dict[str, dict[str, int]], split: Split, seq_len: int, step: int
) -> tuple[np.ndarray, np.ndarray]:

    X_parts: list[np.ndarray] = []
    y_parts: list[np.ndarray] = []
    for i, rec_path in enumerate(recording_files(service_name, split)):
        lines = read_recording(str(rec_path))
        if len(lines) < seq_len + 1:
            continue
        rows = encode_recording(vocabs, lines)
        X, y = make_sequences(rows, seq_len, step)
        if len(X):
            X_parts.append(X)
            y_parts.append(y)
        if (i + 1) % config.RAM_CHECK_EVERY_N_RECORDINGS == 0:
            resource_guard.check_ram(f"{service_name}/{split}: после {i + 1} записей")

    if not X_parts:
        return np.empty((0, seq_len, num_features()), dtype=_SEQ_DTYPE), np.empty((0, seq_len, 1), dtype=_SEQ_DTYPE)

    resource_guard.check_ram(f"{service_name}/{split}: перед склейкой ({len(X_parts)} записей)")
    X_all = np.concatenate(X_parts, axis=0)
    y_all = np.concatenate(y_parts, axis=0)
    resource_guard.check_ram(f"{service_name}/{split}: после склейки ({len(X_all)} окон)")
    return X_all, y_all


def build_test_sequences(
    service_name: str, vocabs: dict[str, dict[str, int]], seq_len: int, step: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    
    normal_files, abnormal_files = test_recording_files(service_name)

    X_parts: list[np.ndarray] = []
    y_parts: list[np.ndarray] = []
    attack_parts: list[np.ndarray] = []

    def process_group(files: list[Path], is_attack: bool) -> None:
        for i, rec_path in enumerate(files):
            lines = read_recording(str(rec_path))
            if len(lines) < seq_len + 1:
                continue
            rows = encode_recording(vocabs, lines)
            X, y = make_sequences(rows, seq_len, step)
            if not len(X):
                continue
            X_parts.append(X)
            y_parts.append(y)
            attack_parts.append(np.full(len(X), is_attack, dtype=bool))
            if (i + 1) % config.RAM_CHECK_EVERY_N_RECORDINGS == 0:
                group = "abnormal" if is_attack else "normal"
                resource_guard.check_ram(f"{service_name}/test/{group}: после {i + 1} записей")

    process_group(normal_files, False)
    process_group(abnormal_files, True)

    if not X_parts:
        return (
            np.empty((0, seq_len, num_features()), dtype=_SEQ_DTYPE),
            np.empty((0, seq_len, 1), dtype=_SEQ_DTYPE),
            np.empty((0,), dtype=bool),
        )

    resource_guard.check_ram(f"{service_name}/test: перед склейкой ({len(X_parts)} записей)")
    X_all = np.concatenate(X_parts, axis=0)
    y_all = np.concatenate(y_parts, axis=0)
    attack_all = np.concatenate(attack_parts, axis=0)
    resource_guard.check_ram(f"{service_name}/test: после склейки ({len(X_all)} окон, "
                              f"{attack_all.sum()} атакующих / {len(attack_all)} всего)")
    return X_all, y_all, attack_all
