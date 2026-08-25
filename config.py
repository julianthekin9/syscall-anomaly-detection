from typing import Literal

DATASET_ROOT = "./DATASET"

SERVICES: list[str] | None = ["FLASK"]

TRAIN_SUBDIR = "training"
VAL_SUBDIR = "validation"
TEST_SUBDIR = "test"

TEST_NORMAL_SUBDIR = "normal"
TEST_ABNORMAL_SUBDIR = "abnormal"

RECORDING_EXTENSION = ".sc"

TIME_COLUMN_INDEX = 0
PROCESS_NAME_COLUMN_INDEX = 1
SYSCALL_COLUMN_INDEX = 2
DIRECTION_COLUMN_INDEX = 3
PARAMS_BEGIN_INDEX = 4  # всё после этого индекса — параметры syscall'а
MIN_RAW_FIELDS = 4

USE_ARG_COUNT_FEATURE = True
ARG_COUNT_BUCKETS = 8  # 0,1,2,...,6, "7+" — clip(arg_count, 0, ARG_COUNT_BUCKETS-1)

VOCAB_DIR = "./vocabs"
FORCE_REBUILD_VOCAB = False

EMBED_DIM_SYSCALL = 16
EMBED_DIM_PROCESS = 8   # эмбеддинг ВХОДНОГО признака process (не голова-предсказатель)
EMBED_DIM_DIRECTION = 2
EMBED_DIM_ARG_COUNT = 4  # используется только если USE_ARG_COUNT_FEATURE=True

HIDDEN_DIM = 128
NUM_LAYERS = 2
DROPOUT = 0.2  # между слоями LSTM при NUM_LAYERS > 1

SEQ_LEN = 64     # длина последовательности (шагов syscall) на один train-пример
SEQ_STEP = 32    # шаг окна при обучении/калибровке (< SEQ_LEN => перекрытие)

BATCH_SIZE = 32
LEARNING_RATE = 1e-3
EPOCHS = 5

RESUME = False

WindowAgg = Literal["quantile", "max"]
WINDOW_AGG: WindowAgg = "quantile"
WINDOW_AGG_QUANTILE = 0.9  # используется только если WINDOW_AGG="quantile"

THRESHOLD_PERCENTILE = 99.0

EVAL_TEST_EVERY_EPOCH = False

METRICS_EVAL_EVERY_N_EPOCHS = 1

TRAIN_METRICS_MAX_BATCHES: int | None = None

MODEL_DIR = "./models"  # <сервис>.pt на каждый сервис — чекпоинт включает веса, словари, порог, гиперпараметры
PLOTS_DIR = "./training_plots"  # <сервис>_epochs.png — график loss/precision по эпохам, см. visualization.py

RAM_GUARD_ENABLED = True
RAM_SOFT_LIMIT_PERCENT = 80.0   # выше -> gc.collect() + пауза + предупреждение, работа продолжается
RAM_HARD_LIMIT_PERCENT = 92.0   # выше -> контролируемая остановка (RamLimitExceeded) вместо SIGKILL
RAM_THROTTLE_SLEEP_SEC = 2.0    # пауза после мягкого срабатывания
RAM_CHECK_EVERY_N_RECORDINGS = 20  # как часто проверять RAM при чтении train/val/test записей