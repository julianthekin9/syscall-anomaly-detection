"""Конфигурация проекта: LSTM предсказывает следующий syscall по
предыдущим N (next-syscall prediction) — модель "нормального поведения" per
service, аномалии детектируются по расхождению реального поведения с
предсказанным (как в оригинальном LID-DS: см. algorithms/decision_engines/lstm.py
и пример со скользящим окном по syscall'ам через Ngram/NgramMinusOne).

Формат датасета — LID-DS 2021: .sc-записи (пробел как разделитель,
абсолютный unix-timestamp в наносекундах) + JSON-метаданные на каждую
запись (exploit/exploit_name/time.exploit[...].absolute).

ВАЖНО про train/val/test: судя по официальному LID-DS, каждый сценарий уже
разбит на 3 части:
    train — ТОЛЬКО нормальное поведение (используется для обучения LSTM)
    val   — ТОЛЬКО нормальное поведение (используется для калибровки порога
            тревоги — held-out нормальные данные, не участвовавшие в train)
    test  — нормальное поведение + атаки (используется для итоговой оценки
            детекции: считаем anomaly score по окнам и сравниваем с порогом)

Имена подпапок под train/val/test — ПРОВЕРЬТЕ на реальной структуре вашего
скачанного датасета и поправьте *_SUBDIR ниже, если названы иначе (например
"training"/"validation"/"test" или "train"/"validation"/"test").
"""

from typing import Literal

# --- Данные -------------------------------------------------------------

LID_DS_ROOT = "./DATASET"

# Какие сценарии (папки) обучать. None = все папки, найденные в LID_DS_ROOT.
SERVICES: list[str] | None = ["FLASK"]

# Имена подпапок train/val/test внутри каждой папки сценария — ПРОВЕРЬТЕ!
TRAIN_SUBDIR = "training"
VAL_SUBDIR = "validation"
TEST_SUBDIR = "test"

# Внутри TEST_SUBDIR ожидаются ДВЕ подпапки — test-сплит размечается ЦЕЛОЙ
# ЗАПИСЬЮ (без JSON, без построчного timestamp'а): всё, что лежит в
# TEST_ABNORMAL_SUBDIR, целиком считается атакующим, всё, что в
# TEST_NORMAL_SUBDIR, — целиком нормальным. Структура на диске:
#   <LID_DS_ROOT>/<сценарий>/<TEST_SUBDIR>/<TEST_NORMAL_SUBDIR>/*.sc
#   <LID_DS_ROOT>/<сценарий>/<TEST_SUBDIR>/<TEST_ABNORMAL_SUBDIR>/*.sc
TEST_NORMAL_SUBDIR = "normal"
TEST_ABNORMAL_SUBDIR = "abnormal"

RECORDING_EXTENSION = ".sc"

# --- Формат строки .sc-файла (LID-DS 2021) -------------------------------
# TIMESTAMP(unix ns, абсолютный) USER_ID PROCESS_ID PROCESS_NAME THREAD_ID
# SYSCALL_NAME DIRECTION [params...]
TIME_COLUMN_INDEX = 0
PROCESS_NAME_COLUMN_INDEX = 3
SYSCALL_COLUMN_INDEX = 5
DIRECTION_COLUMN_INDEX = 6
PARAMS_BEGIN_INDEX = 7  # всё после этого индекса — параметры syscall'а
MIN_RAW_FIELDS = 7

# --- Признаки модели ------------------------------------------------------

# Базовые признаки — всегда используются: syscall, process, direction.
# Аргументы syscall'ов в сыром виде (адреса памяти, base64-блобы, файловые
# дескрипторы) плохо поддаются осмысленному эмбеддингу без специальной
# обработки под каждый syscall отдельно — вместо этого используем ПРОСТОЙ
# числовой прокси-признак: количество переданных параметров, забакеченное
# в небольшое число корзин. Это не полноценный анализ аргументов, но даёт
# модели сигнал "необычное число параметров для этого syscall'а" почти
# бесплатно. Полноценный разбор конкретных значений — за рамками этого
# проекта, можно расширять точечно под конкретный syscall при необходимости.
USE_ARG_COUNT_FEATURE = True
ARG_COUNT_BUCKETS = 8  # 0,1,2,...,6, "7+" — clip(arg_count, 0, ARG_COUNT_BUCKETS-1)

# --- Словари (syscall/process/direction) --------------------------------

# build_vocab() кэширует словари на диск (<сервис>.json в VOCAB_DIR) — это
# позволяет не перечитывать весь train-сплит заново при каждом запуске
# train.py/predict.py. Кэш валиден, пока не поменялась логика парсинга или
# сам train-сплит; если поменяли данные/парсинг — либо удалите файл(ы) в
# VOCAB_DIR вручную, либо выставьте FORCE_REBUILD_VOCAB=True на один запуск.
VOCAB_DIR = "./vocabs"
FORCE_REBUILD_VOCAB = False

# --- Гиперпараметры модели -------------------------------------------------

EMBED_DIM_SYSCALL = 16
EMBED_DIM_PROCESS = 8
EMBED_DIM_DIRECTION = 2
EMBED_DIM_ARG_COUNT = 4  # используется только если USE_ARG_COUNT_FEATURE=True

HIDDEN_DIM = 128
NUM_LAYERS = 2
DROPOUT = 0.2  # между слоями LSTM при NUM_LAYERS > 1

# --- Скользящее окно (авторегрессионные последовательности) ---------------

SEQ_LEN = 64     # длина последовательности (шагов syscall) на один train-пример
SEQ_STEP = 32    # шаг окна при обучении/калибровке (< SEQ_LEN => перекрытие)
# Для инференса на новом логе используем шаг = SEQ_LEN (без перекрытия) —
# каждое событие лога учитывается ровно в одном окне, см. predict.py

# --- Гиперпараметры обучения ------------------------------------------------

BATCH_SIZE = 32
LEARNING_RATE = 1e-3
EPOCHS = 5


RESUME = False

# --- Anomaly score / порог тревоги ------------------------------------------

# "nll"   — negative log-likelihood истинного следующего syscall'а (чем
#           меньше модель верила в реальный syscall, тем выше score)
# "top_k" — 1, если истинный syscall НЕ попал в top-k предсказанных
#           (классический STIDE-подход)
ScoreMethod = Literal["nll", "top_k"]
SCORE_METHOD: ScoreMethod = "nll"
TOP_K = 5  # используется только при SCORE_METHOD="top_k"

# --- Агрегация anomaly score внутри окна ------------------------------------
#
# Проблема, из-за которой модель может почти идеально предсказывать
# syscall'ы (низкий perplexity), но при этом НЕ детектировать атаку:
# если атака короче ~10% окна (при SEQ_LEN=64 это ~7 шагов), то при
# агрегации "квантиль 0.9" всплеск NLL на шагах атаки тонет среди
# соседних низких (нормальных) значений — итоговый score окна остаётся
# ниже порога, откалиброванного на val.
#
# "max"      — score окна = худший (самый аномальный) шаг окна. Ловит
#              атаку любой длины >=1 шаг внутри окна, независимо от
#              SEQ_LEN. Более чувствителен, но и более шумный — одна
#              редкая, но легитимная комбинация syscall'ов может дать
#              ложный алерт.
# "quantile" — старое поведение (нужен минимум WINDOW_AGG_QUANTILE-доля
#              "плохих" шагов в окне, чтобы score окна вырос).
WindowAgg = Literal["quantile", "max"]
WINDOW_AGG: WindowAgg = "quantile"
WINDOW_AGG_QUANTILE = 0.9  # используется только если WINDOW_AGG="quantile"

# Порог калибруется на held-out НОРМАЛЬНОМ val-сплите (ровно для этого он в
# LID-DS и предусмотрен) — берётся этот перцентиль распределения anomaly
# score по окнам val. Например, 99.0 => ожидаемый false positive rate на
# чистом нормальном трафике ~1%.
THRESHOLD_PERCENTILE = 99.0

# --- Multi-task: вторая голова модели (process) ------------------------
#
# Помимо next-syscall модель также предсказывает next-process — полезно,
# когда сама атака не создаёт необычной последовательности syscall'ов, но
# создаёт необычный ПРОЦЕСС (классика для web-shell/RCE: веб-сервер
# внезапно порождает shell/другой процесс — syscall'ы при этом самые
# обычные execve/read/write, а появление процесса, которого не было в
# train, — очень сильный сигнал сам по себе). См. model.SyscallLSTM.
PROCESS_LOSS_WEIGHT = 1.0    # вес process-головы в train loss: syscall_loss + вес * process_loss
PROCESS_SCORE_WEIGHT = 1.0   # вес process anomaly score при объединении со syscall score (окно/порог/детекция)

# Если True — порог и diagnostics-метрики (classification_report, ROC-AUC)
# на test-сплите считаются после КАЖДОЙ эпохи, не только после последней —
# удобно видеть, как качество детекции меняется по ходу обучения. Это
# лишний полный проход по test каждую эпоху (forward без backward, но всё
# равно занимает время) — на большом test-сплите заметно замедлит обучение.
# При False оценка считается один раз, после последней эпохи (как раньше).
EVAL_TEST_EVERY_EPOCH = False

# --- Метрики train/val по эпохам (для графика, см. visualization.py) -------
#
# Раз в METRICS_EVAL_EVERY_N_EPOCHS эпох (1 = каждую) считаем ПОЛНЫЙ eval-
# проход (model.eval(), без dropout/backward) отдельно по train и по val:
# loss + macro-precision по next-syscall (и next-process, если голова
# включена). Это ДОПОЛНИТЕЛЬНЫЙ полный forward-проход по train на каждую
# такую эпоху — на большом train заметно замедляет обучение, отсюда и
# настройка "раз в N эпох", а не всегда.
METRICS_EVAL_EVERY_N_EPOCHS = 1

# Ограничить train-проход первыми N батчами train_loader (None = весь
# train). Компромисс точность/скорость: на очень большом train полная
# оценка может быть непозволительно долгой каждые N эпох.
TRAIN_METRICS_MAX_BATCHES: int | None = None

# --- Пути ------------------------------------------------------------------

MODEL_DIR = "./models"  # <сервис>.pt на каждый сервис — чекпоинт включает веса, словари, порог, гиперпараметры
PLOTS_DIR = "./training_plots"  # <сервис>_epochs.png — график loss/precision по эпохам, см. visualization.py

RANDOM_STATE = 42  # зарезервировано под воспроизводимость будущих random-сплитов
# ПРИМЕЧАНИЕ: сейчас нигде не используется как torch/numpy seed — обучение
# (порядок батчей в DataLoader shuffle=True) не детерминировано между
# запусками. Если нужна полная воспроизводимость, добавьте в train.py
# torch.manual_seed(config.RANDOM_STATE) и random.seed(...)/np.random.seed(...)
# перед созданием DataLoader'ов.

# --- Защита от OOM (resource_guard.py) --------------------------------------
#
# Основное снижение потребления памяти — в data.py (последовательности
# хранятся как numpy int32/int64, а не как вложенные списки Python-объектов).
# Это — страховка НА СЛУЧАЙ, если памяти всё равно не хватает (большой
# train-сплит, большой SEQ_LEN/BATCH_SIZE): вместо того чтобы дать OOM
# killer молча прибить процесс (SIGKILL, без трейсбека), проверяем текущую
# загрузку RAM в горячих местах (построение последовательностей, начало
# каждой эпохи) и реагируем заранее.
RAM_GUARD_ENABLED = True
RAM_SOFT_LIMIT_PERCENT = 80.0   # выше -> gc.collect() + пауза + предупреждение, работа продолжается
RAM_HARD_LIMIT_PERCENT = 92.0   # выше -> контролируемая остановка (RamLimitExceeded) вместо SIGKILL
RAM_THROTTLE_SLEEP_SEC = 2.0    # пауза после мягкого срабатывания
RAM_CHECK_EVERY_N_RECORDINGS = 20  # как часто проверять RAM при чтении train/val/test записей