"""Парсинг LID-DS 2021 (.sc), построение словарей и авторегрессионных
последовательностей (next-syscall + next-process prediction) для train/
val/test сплитов.

Разметка test-сплита — ЦЕЛОЙ ЗАПИСЬЮ, без JSON и без построчного сравнения
timestamp'ов: test-сплит ожидается в виде двух подпапок,
config.TEST_NORMAL_SUBDIR (целиком нормальные записи) и
config.TEST_ABNORMAL_SUBDIR (целиком атакующие записи) — все окна из файлов
в normal/ размечаются как норма, все окна из файлов в abnormal/ — как атака.
Как и для train/val, JSON-метаданные вообще не читаются.
"""

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
    """Одна распарсенная строка .sc-записи."""

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
    """True, если LID_DS_ROOT указывает ПРЯМО на папку одного сценария
    (training/validation/test лежат прямо внутри LID_DS_ROOT), а не на
    корень с несколькими подпапками-сценариями. Типичная ситуация, когда
    скачан только один CVE-сценарий, а не весь корпус LID-DS."""
    root = Path(config.LID_DS_ROOT)
    return (root / config.TRAIN_SUBDIR).is_dir() and (root / config.TEST_SUBDIR).is_dir()


def list_services() -> list[str]:
    """Список сервисов (папок сценариев) под LID_DS_ROOT.

    Поддерживает две структуры датасета:
    - LID_DS_ROOT/<сценарий>/<training|validation|test>/...  (несколько
      сценариев под одним корнем — обычный случай для полного корпуса LID-DS)
    - LID_DS_ROOT/<training|validation|test>/...  (LID_DS_ROOT указывает
      прямо на папку ОДНОГО сценария — типично, если скачан один CVE)
    Определяется автоматически по наличию TRAIN_SUBDIR/TEST_SUBDIR прямо
    внутри LID_DS_ROOT — переносить файлы на диске не нужно.
    """
    root = Path(config.LID_DS_ROOT)
    if not root.exists():
        raise FileNotFoundError(f"Не найдена LID_DS_ROOT={root} — проверьте config.LID_DS_ROOT.")

    if _root_is_single_service():
        names = [root.name]
    else:
        names = sorted(p.name for p in root.iterdir() if p.is_dir())

    if config.SERVICES is not None:
        names = [n for n in names if n in config.SERVICES]
    return names


def _split_dir(service_name: str, split: Split) -> Path:
    root = Path(config.LID_DS_ROOT)
    if _root_is_single_service() and service_name == root.name:
        return root / _SPLIT_SUBDIR[split]
    return root / service_name / _SPLIT_SUBDIR[split]


def recording_files(service_name: str, split: Split) -> list[Path]:
    """Список .sc-файлов конкретного сплита конкретного сервиса.
    Для split="test" ищет ПРЯМО внутри test-папки — если у вас test уже
    разложен на normal/abnormal (см. test_recording_files), этот метод не
    различает их и просто найдёт все .sc рекурсивно; для diagnostics-оценки
    используйте test_recording_files, а не эту функцию."""
    split_dir = _split_dir(service_name, split)
    if not split_dir.exists():
        raise FileNotFoundError(
            f"Не найдена папка сплита {split_dir} — проверьте config.{split.upper()}_SUBDIR "
            f"на соответствие реальной структуре датасета (ожидается либо "
            f"LID_DS_ROOT/<сценарий>/<{split}-подпапка>, либо, если LID_DS_ROOT "
            f"уже указывает на папку одного сценария, LID_DS_ROOT/<{split}-подпапка>)."
        )
    return sorted(split_dir.rglob(f"*{config.RECORDING_EXTENSION}"))


def test_recording_files(service_name: str) -> tuple[list[Path], list[Path]]:
    """.sc-файлы test-сплита, разделённые на нормальные и атакующие ЦЕЛЫМИ
    ЗАПИСЯМИ (по тому, в какой подпапке лежат) — без JSON, без построчной
    разметки по timestamp'у. Ожидаемая структура:
        <test-сплит>/<config.TEST_NORMAL_SUBDIR>/*.sc   — целиком нормальные записи
        <test-сплит>/<config.TEST_ABNORMAL_SUBDIR>/*.sc — целиком атакующие записи
    Возвращает (normal_files, abnormal_files).
    """
    test_dir = _split_dir(service_name, "test")
    normal_dir = test_dir / config.TEST_NORMAL_SUBDIR
    abnormal_dir = test_dir / config.TEST_ABNORMAL_SUBDIR
    if not normal_dir.is_dir() or not abnormal_dir.is_dir():
        raise FileNotFoundError(
            f"Ожидались подпапки {normal_dir} и {abnormal_dir} — проверьте "
            f"config.TEST_NORMAL_SUBDIR/config.TEST_ABNORMAL_SUBDIR на соответствие "
            f"реальной структуре test-сплита."
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
    """X/y хранятся как int16 (см. _SEQ_DTYPE) ради компактности в памяти —
    словари syscall/process/direction в LID-DS обычно ~10-100 значений, но
    если вдруг словарь окажется больше 32767 (маловероятно, но лучше упасть
    явно, чем тихо получить переполнение int16 и порченные индексы)."""
    limit = np.iinfo(_SEQ_DTYPE).max
    too_big = {name: len(v) for name, v in vocabs.items() if len(v) > limit}
    if too_big:
        raise ValueError(
            f"Словари {too_big} превышают ёмкость {_SEQ_DTYPE.__name__} (макс {limit}) — "
            f"поменяйте data._SEQ_DTYPE на np.int32 вручную, если у вас настолько большие словари."
        )


def build_vocab(service_name: str, use_cache: bool = True) -> dict[str, dict[str, int]]:
    """Строит словари syscall/process/direction ТОЛЬКО по train-сплиту (чисто
    нормальное поведение). Syscall'ы, впервые появляющиеся во время атаки в
    test-сплите, будут кодироваться как UNK — это осознанно: незнакомый
    syscall сам по себе является сильным сигналом аномалии.

    Если use_cache=True (по умолчанию) и на диске уже есть закэшированный
    словарь (config.VOCAB_DIR/<сервис>.json) — читает его, не перечитывая
    весь train-сплит заново. Кэш ничего не знает о том, менялись ли данные
    или логика парсинга с прошлого запуска — при необходимости сносите файл
    вручную или ставьте config.FORCE_REBUILD_VOCAB=True на один прогон.
    """
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
    """Кодирует все строки записи в ОДИН numpy-массив [len(lines), num_features]
    (int16) вместо списка списков Python int'ов — на порядок компактнее в
    памяти (int16-ячейка в numpy-массиве занимает 2 байта; Python int-объект
    в списке — от ~28 байт плюс накладные расходы самого списка), что на
    больших .sc-записях напрямую снижает риск OOM."""
    arr = np.empty((len(lines), num_features()), dtype=_SEQ_DTYPE)
    for i, line in enumerate(lines):
        arr[i, :] = encode_line(vocabs, line)
    return arr


def make_sequences(rows: np.ndarray, seq_len: int, step: int) -> tuple[np.ndarray, np.ndarray]:
    """Режет закодированный numpy-массив rows [n, num_features] на
    last-token-prediction окна.

    X: [n_windows, seq_len, num_features] int16 — вход, все признаки
    y: [n_windows, seq_len, 2] int16 — ДВА таргета на каждый шаг:
       y[..., 0] = id syscall'а на следующем шаге (rows[:, 0])
       y[..., 1] = id process'а на следующем шаге (rows[:, 1])
       (см. model.SyscallLSTM — модель предсказывает оба: помимо
       "неожиданный syscall" это ловит и "неожиданный процесс", что важно
       для атак, не создающих аномальной последовательности syscall'ов, но
       порождающих аномальный процесс — например web-shell/RCE).

    Возвращает пустые массивы (0 окон), если rows короче seq_len+1.

    ПРИМЕЧАНИЕ про память: при SEQ_STEP < SEQ_LEN окна перекрываются, то
    есть каждый syscall физически копируется в память несколько раз (это
    нужно для аугментации train-данных) — это не баг, но именно поэтому
    здесь используются компактные int16, а не списки Python-объектов или
    int32/int64, и почему уменьшение перекрытия (увеличение SEQ_STEP) —
    рабочий способ снизить пиковое потребление памяти, если она всё равно
    кончается.
    """
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
    """Последовательности из чисто нормального сплита (train или val) — без
    разметки атак, т.к. по определению датасета там атак нет.

    Собирает numpy-массив по каждой записи отдельно и склеивает их в конце
    ОДНИМ np.concatenate — вместо построчного extend() в Python-список, что
    и обеспечивает основную экономию памяти (см. make_sequences)."""
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
    """Последовательности из test-сплита (normal/ + abnormal/ подпапки) +
    метка окна для diagnostics-оценки в predict.py.

    Разметка — ЦЕЛОЙ ЗАПИСЬЮ: ВСЕ окна из файлов в config.TEST_ABNORMAL_SUBDIR
    размечаются как атака (window_is_attack=True), ВСЕ окна из файлов в
    config.TEST_NORMAL_SUBDIR — как норма. JSON не читается, построчная
    разметка по timestamp'у не считается — в отличие от предыдущей версии,
    где атака размечалась по meta["time"]["exploit"][0]["absolute"].

    Используется ТОЛЬКО для оценки качества детекции постфактум, не
    участвует в детекции как таковой — сама LSTM-модель обучается
    исключительно на train/val, про атаки "не знает".
    """
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