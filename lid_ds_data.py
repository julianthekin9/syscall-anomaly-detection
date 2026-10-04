"""
Завантаження датасету LID-DS 2021 з тим самим інтерфейсом, що й у data.py:
list_services, build_vocab, build_normal_sequences, build_test_sequences (+ read_recording).

Структура: DATASET_ROOT/<сценарій>/{training,validation,test}/...
Запис — це або <ім'я>.zip (всередині <ім'я>.sc та <ім'я>.json), або розпакована
пара <ім'я>.sc + <ім'я>.json в одній теці.

Формат рядка .sc (LID-DS 2021):
    <time_ns> <uid> <pid> <process> <tid> <syscall> <dir> <params...>

Навчальна та валідаційна вибірки — лише послідовності (як у data.py).
Тестова вибірка розмічається за часом: початок атаки береться з <ім'я>.json
(time.exploit[*].absolute, unix-секунди), а вікно вважається атакуючим, якщо частка
його цільових кроків із часом >= початку атаки не менша за config.LID_DS_ATTACK_MIN_FRACTION.
Підтеки test/normal та test/normal_and_attack не використовуються — тип запису
визначається лише полем "exploit" у json.
"""

import json
import zipfile
from array import array
from pathlib import Path
from typing import Iterator

import numpy as np

import config
import data
import resource_guard
from data import ParsedLine, Split, list_services  # noqa: F401  (list_services реекспортується)

_TIME_IDX = 0
_PROCESS_IDX = 3
_SYSCALL_IDX = 5
_DIRECTION_IDX = 6
_PARAMS_IDX = 7
_DIRECTIONS = (">", "<")


# ---------------------------------------------------------------- читання записів

def _find_member(zf: zipfile.ZipFile, extension: str) -> str:
    for name in zf.namelist():
        if name.endswith(extension):
            return name
    raise FileNotFoundError(f"У {zf.filename} немає файлу *{extension}")


def _iter_lines(path: Path) -> Iterator[str]:
    """Потоково віддає рядки .sc — з zip або з розпакованого файлу."""
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as zf:
            with zf.open(_find_member(zf, ".sc")) as raw:
                for line in raw:
                    yield line.decode("utf-8", errors="ignore")
    else:
        with open(path, encoding="utf-8", errors="ignore") as f:
            yield from f


def parse_lid_ds_line(line: str) -> ParsedLine | None:
    """Парсить один рядок LID-DS .sc. None для "сміттєвих" рядків та подій switch."""
    line = line.rstrip()
    fields = line.split(" ", _PARAMS_IDX)

    if len(fields) > _DIRECTION_IDX and fields[_DIRECTION_IDX] in _DIRECTIONS:
        # швидкий шлях: ім'я процесу без пробілів
        time_str = fields[_TIME_IDX]
        process_name = fields[_PROCESS_IDX]
        syscall = fields[_SYSCALL_IDX]
        direction = fields[_DIRECTION_IDX]
        params = fields[_PARAMS_IDX] if len(fields) > _PARAMS_IDX else ""
        arg_count = params.count(" ") + 1 if params else 0
    else:
        # повільний шлях: ім'я процесу з пробілами (напр. "C2 CompilerThre" у ZipSlip)
        tokens = line.split(" ")
        d = next((i for i in range(_DIRECTION_IDX, len(tokens)) if tokens[i] in _DIRECTIONS), None)
        if d is None:
            return None
        time_str = tokens[_TIME_IDX]
        process_name = "_".join(tokens[_PROCESS_IDX:d - 2])
        syscall = tokens[d - 1]
        direction = tokens[d]
        arg_count = len(tokens) - d - 1

    if syscall == "switch":
        return None
    try:
        timestamp_ns = int(time_str)
    except ValueError:
        return None

    return ParsedLine(
        timestamp=timestamp_ns / 1e9,
        syscall=syscall,
        process_name=process_name,
        direction=direction,
        arg_count=arg_count,
    )


def read_recording(path: str) -> list[ParsedLine]:
    """Аналог data.read_recording для формату LID-DS (для predict.py --log)."""
    lines: list[ParsedLine] = []
    for raw in _iter_lines(Path(path)):
        parsed = parse_lid_ds_line(raw)
        if parsed is not None:
            lines.append(parsed)
    return lines


def read_encoded(path: Path, vocabs: dict[str, dict[str, int]], keep_time: bool) -> tuple[np.ndarray, np.ndarray | None]:
    """
    Потоково кодує запис у масив ознак [N, num_features] (+ масив часу [N] у секундах).
    Проміжні дані зберігаються в array.array, а не в списках Python-об'єктів, щоб не впертись в RAM.
    """
    n_feat = data.num_features()
    columns = [array("i") for _ in range(n_feat)]
    times = array("d")

    for raw in _iter_lines(path):
        parsed = parse_lid_ds_line(raw)
        if parsed is None:
            continue
        for column, value in zip(columns, data.encode_line(vocabs, parsed)):
            column.append(value)
        if keep_time:
            times.append(parsed.timestamp)

    n = len(columns[0])
    rows = np.empty((n, n_feat), dtype=data._SEQ_DTYPE)
    if n == 0:
        return rows, (np.empty((0,), dtype=np.float64) if keep_time else None)
    for j, column in enumerate(columns):
        rows[:, j] = np.frombuffer(column, dtype=np.int32)
    return rows, (np.frombuffer(times, dtype=np.float64) if keep_time else None)


# ---------------------------------------------------------------- файли та метадані

def recording_files(service_name: str, split: Split) -> list[Path]:
    split_dir = data._split_dir(service_name, split)
    if not split_dir.exists():
        raise FileNotFoundError(f"Не знайдено теку спліту {split_dir} (config.DATASET_ROOT={config.DATASET_ROOT})")

    found: dict[Path, Path] = {}
    for path in sorted(split_dir.rglob("*")):
        if path.suffix not in (".zip", ".sc"):
            continue
        key = path.with_suffix("")
        # якщо є і zip, і розпакований .sc — віддаємо перевагу розпакованому
        if key not in found or path.suffix == ".sc":
            found[key] = path
    return sorted(found.values())


def load_metadata(path: Path) -> dict:
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as zf:
            text = zf.read(_find_member(zf, ".json")).decode("utf-8")
    else:
        text = path.with_suffix(".json").read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(text.replace("'", '"'))  # як у dataloader LID-DS


def attack_start_ts(meta: dict) -> float | None:
    """Початок атаки (unix-секунди) або None для запису без експлойту."""
    if not meta.get("exploit"):
        return None
    times = [e["absolute"] for e in meta.get("time", {}).get("exploit", []) if e.get("absolute") is not None]
    if not times:
        raise ValueError('"exploit": true, але time.exploit порожній')
    return float(min(times))


# ---------------------------------------------------------------- словник

def vocab_path(service_name: str) -> Path:
    # окремий файл, щоб кеш не змішувався зі словниками "довільних" датасетів
    return Path(config.VOCAB_DIR) / f"{service_name}.lid_ds.json"


def build_vocab(service_name: str, use_cache: bool = True) -> dict[str, dict[str, int]]:
    path = vocab_path(service_name)
    if use_cache and path.exists():
        with open(path, encoding="utf-8") as f:
            cached = json.load(f)
        data._check_vocab_fits_dtype(cached)
        return cached

    raw_values: dict[str, set] = {name: set() for name in data.FEATURE_NAMES}
    for rec_path in recording_files(service_name, "train"):
        for raw in _iter_lines(rec_path):
            parsed = parse_lid_ds_line(raw)
            if parsed is None:
                continue
            raw_values["syscall"].add(parsed.syscall)
            raw_values["process"].add(parsed.process_name)
            raw_values["direction"].add(parsed.direction)

    vocabs: dict[str, dict[str, int]] = {}
    for name in data.FEATURE_NAMES:
        vocab = {data.PAD: 0, data.UNK: 1}
        vocab.update({value: i + 2 for i, value in enumerate(sorted(raw_values[name]))})
        vocabs[name] = vocab

    data._check_vocab_fits_dtype(vocabs)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(vocabs, f, ensure_ascii=False, indent=2)
    return vocabs


# ---------------------------------------------------------------- вікна

def _window_starts(n: int, seq_len: int, step: int) -> np.ndarray:
    """Має збігатися з логікою вибору вікон у data.make_sequences (потрібно n >= seq_len + 1)."""
    needed = seq_len + 1
    starts = list(range(0, n - needed + 1, step))
    if starts[-1] + needed < n:
        starts.append(n - needed)
    return np.asarray(starts, dtype=np.int64)


def _gather_windows(rows: np.ndarray, starts: np.ndarray, seq_len: int) -> tuple[np.ndarray, np.ndarray]:
    idx = starts[:, None] + np.arange(seq_len)[None, :]  # [W, seq_len]
    X = rows[idx]                                        # [W, seq_len, F]
    y = rows[idx + 1, 0][..., None]                      # наступний syscall, [W, seq_len, 1]
    return X, y


def _window_labels(times: np.ndarray, starts: np.ndarray, seq_len: int, attack_ts: float | None) -> np.ndarray:
    """Вікно — атакуюче, якщо частка цільових кроків (events s+1..s+seq_len) з часом >= attack_ts достатня."""
    if attack_ts is None:
        return np.zeros(len(starts), dtype=bool)
    prefix = np.concatenate(([0], np.cumsum(times >= attack_ts)))
    attack_steps = prefix[starts + seq_len + 1] - prefix[starts + 1]
    return attack_steps / seq_len >= config.LID_DS_ATTACK_MIN_FRACTION


def build_normal_sequences(
    service_name: str, vocabs: dict[str, dict[str, int]], split: Split, seq_len: int, step: int
) -> tuple[np.ndarray, np.ndarray]:
    X_parts: list[np.ndarray] = []
    y_parts: list[np.ndarray] = []
    for i, rec_path in enumerate(recording_files(service_name, split)):
        rows, _ = read_encoded(rec_path, vocabs, keep_time=False)
        if len(rows) < seq_len + 1:
            continue
        X, y = data.make_sequences(rows, seq_len, step)
        if len(X):
            X_parts.append(X)
            y_parts.append(y)
        if (i + 1) % config.RAM_CHECK_EVERY_N_RECORDINGS == 0:
            resource_guard.check_ram(f"{service_name}/{split}: після {i + 1} записів")

    if not X_parts:
        return (
            np.empty((0, seq_len, data.num_features()), dtype=data._SEQ_DTYPE),
            np.empty((0, seq_len, 1), dtype=data._SEQ_DTYPE),
        )

    resource_guard.check_ram(f"{service_name}/{split}: перед склейкою ({len(X_parts)} записів)")
    X_all = np.concatenate(X_parts, axis=0)
    y_all = np.concatenate(y_parts, axis=0)
    resource_guard.check_ram(f"{service_name}/{split}: після склейки ({len(X_all)} вікон)")
    return X_all, y_all


def build_test_sequences(
    service_name: str, vocabs: dict[str, dict[str, int]], seq_len: int, step: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    X_parts: list[np.ndarray] = []
    y_parts: list[np.ndarray] = []
    attack_parts: list[np.ndarray] = []
    n_attack_recordings = 0

    files = recording_files(service_name, "test")
    for i, rec_path in enumerate(files):
        try:
            attack_ts = attack_start_ts(load_metadata(rec_path))
        except (ValueError, OSError, zipfile.BadZipFile) as exc:
            print(f"[{service_name}] test: пропускаю {rec_path.name} — {exc}")
            continue

        rows, times = read_encoded(rec_path, vocabs, keep_time=True)
        if len(rows) < seq_len + 1:
            continue
        starts = _window_starts(len(rows), seq_len, step)
        X, y = _gather_windows(rows, starts, seq_len)
        X_parts.append(X)
        y_parts.append(y)
        attack_parts.append(_window_labels(times, starts, seq_len, attack_ts))
        n_attack_recordings += attack_ts is not None
        if (i + 1) % config.RAM_CHECK_EVERY_N_RECORDINGS == 0:
            resource_guard.check_ram(f"{service_name}/test: після {i + 1} записів")

    if not X_parts:
        return (
            np.empty((0, seq_len, data.num_features()), dtype=data._SEQ_DTYPE),
            np.empty((0, seq_len, 1), dtype=data._SEQ_DTYPE),
            np.empty((0,), dtype=bool),
        )

    resource_guard.check_ram(f"{service_name}/test: перед склейкою ({len(X_parts)} записів)")
    X_all = np.concatenate(X_parts, axis=0)
    y_all = np.concatenate(y_parts, axis=0)
    attack_all = np.concatenate(attack_parts, axis=0)
    print(
        f"[{service_name}] test: {len(X_parts)} записів ({n_attack_recordings} з атакою), "
        f"вікон {len(attack_all)}, з них атакуючих {int(attack_all.sum())}"
    )
    return X_all, y_all, attack_all
