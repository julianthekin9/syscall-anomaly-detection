import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np

import config
import resource_guard

PAD = "<PAD>"
UNK = "<UNK>"
FEATURE_NAMES = ["syscall", "process", "direction"]  # + "arg_count", если config.USE_ARG_COUNT_FEATURE

Split = Literal["train", "val", "test"]

_SPLIT_SUBDIR = {
    "train": config.TRAIN_SUBDIR,
    "val": config.VAL_SUBDIR,
    "test": config.TEST_SUBDIR,
}

@dataclass
class ParsedLine:
    timestamp: float  # абсолютные unix-секунды
    syscall: str
    process_name: str
    direction: str
    arg_count: int


def parse_log_line(line: str) -> ParsedLine | None:
    """Парсит одну строку .sc-записи. Возвращает None для "мусорных" строк."""
    fields = line.strip().split(" ")
    if len(fields) < config.MIN_RAW_FIELDS:
        return None

    try:
        timestamp_ns = int(fields[config.TIME_COLUMN_INDEX])
    except (ValueError, IndexError):
        return None

    try:
        syscall = fields[config.SYSCALL_COLUMN_INDEX]
        process_name = fields[config.PROCESS_NAME_COLUMN_INDEX]
        direction = fields[config.DIRECTION_COLUMN_INDEX]
    except IndexError:
        return None

    arg_count = max(0, len(fields) - config.PARAMS_BEGIN_INDEX)

    return ParsedLine(
        timestamp=timestamp_ns / 1e9,
        syscall=syscall,
        process_name=process_name,
        direction=direction,
        arg_count=arg_count,
    )


def read_recording(path: str) -> list[ParsedLine]:
    """Читает один .sc-файл и возвращает список распарсенных строк (без 'switch')."""
    lines: list[ParsedLine] = []
    with open(path, encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            parsed = parse_log_line(raw_line)
            if parsed is not None and parsed.syscall != "switch":
                lines.append(parsed)
    return lines


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
        return np.empty((0, seq_len, n_feat), dtype=_SEQ_DTYPE), np.empty((0, seq_len, 2), dtype=_SEQ_DTYPE)

    starts = list(range(0, n - needed + 1, step))
    last_start = starts[-1] if starts else 0
    if last_start + needed < n:
        starts.append(n - needed)  # прижимаем последнее окно к концу, не теряя хвост

    n_windows = len(starts)
    X = np.empty((n_windows, seq_len, n_feat), dtype=_SEQ_DTYPE)
    y = np.empty((n_windows, seq_len, 2), dtype=_SEQ_DTYPE)
    for i, start in enumerate(starts):
        chunk = rows[start : start + needed]
        X[i] = chunk[:-1]
        y[i, :, 0] = chunk[1:, 0]  # next syscall
        y[i, :, 1] = chunk[1:, 1]  # next process
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
        return np.empty((0, seq_len, num_features()), dtype=_SEQ_DTYPE), np.empty((0, seq_len, 2), dtype=_SEQ_DTYPE)

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
            np.empty((0, seq_len, 2), dtype=_SEQ_DTYPE),
            np.empty((0,), dtype=bool),
        )

    resource_guard.check_ram(f"{service_name}/test: перед склейкой ({len(X_parts)} записей)")
    X_all = np.concatenate(X_parts, axis=0)
    y_all = np.concatenate(y_parts, axis=0)
    attack_all = np.concatenate(attack_parts, axis=0)
    resource_guard.check_ram(f"{service_name}/test: после склейки ({len(X_all)} окон, "
                              f"{attack_all.sum()} атакующих / {len(attack_all)} всего)")
    return X_all, y_all, attack_all