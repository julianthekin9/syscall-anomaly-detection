"""Конфіг пакета.

Параметри експерименту читаються з config.yaml поруч із цим файлом і виставляються
як атрибути модуля (config.SEQ_LEN тощо). Тут же, константами, лишається опис формату
трас: це не налаштування експерименту, а контракт із eBPF-колектором і конвертером LID-DS.
"""

from pathlib import Path
from typing import Literal

import yaml

CONFIG_PATH = Path(__file__).with_name("config.yaml")

# --- Формат трас (не параметри експерименту) ---
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

# --- Параметри експерименту з config.yaml ---
with open(CONFIG_PATH, encoding="utf-8") as _f:
    _cfg: dict = yaml.safe_load(_f)

# pop: відсутній ключ дає KeyError з його ім'ям, а залишок після розбору — невідомі ключі
DATASET_ROOT: str = _cfg.pop("dataset_root")
SERVICES: list[str] | None = _cfg.pop("services")

USE_ARG_COUNT_FEATURE: bool = _cfg.pop("use_arg_count_feature")
ARG_COUNT_BUCKETS: int = _cfg.pop("arg_count_buckets")
FORCE_REBUILD_VOCAB: bool = _cfg.pop("force_rebuild_vocab")

EMBED_DIM_SYSCALL: int = _cfg.pop("embed_dim_syscall")
EMBED_DIM_PROCESS: int = _cfg.pop("embed_dim_process")
EMBED_DIM_DIRECTION: int = _cfg.pop("embed_dim_direction")
EMBED_DIM_ARG_COUNT: int = _cfg.pop("embed_dim_arg_count")
HIDDEN_DIM: int = _cfg.pop("hidden_dim")
NUM_LAYERS: int = _cfg.pop("num_layers")
DROPOUT: float = _cfg.pop("dropout")

SEQ_LEN: int = _cfg.pop("seq_len")
SEQ_STEP: int = _cfg.pop("seq_step")

BATCH_SIZE: int = _cfg.pop("batch_size")
LEARNING_RATE: float = _cfg.pop("learning_rate")
EPOCHS: int = _cfg.pop("epochs")
RESUME: bool = _cfg.pop("resume")

WindowAgg = Literal["quantile", "max"]
WINDOW_AGG: WindowAgg = _cfg.pop("window_agg")
WINDOW_AGG_QUANTILE: float = _cfg.pop("window_agg_quantile")
THRESHOLD_PERCENTILE: float = _cfg.pop("threshold_percentile")

EVAL_TEST_EVERY_EPOCH: bool = _cfg.pop("eval_test_every_epoch")
METRICS_EVAL_EVERY_N_EPOCHS: int = _cfg.pop("metrics_eval_every_n_epochs")
TRAIN_METRICS_MAX_BATCHES: int | None = _cfg.pop("train_metrics_max_batches")

MODEL_DIR: str = _cfg.pop("model_dir")
CHECKPOINT_DIR: str = _cfg.pop("checkpoint_dir")
VOCAB_DIR: str = _cfg.pop("vocab_dir")
PLOTS_DIR: str = _cfg.pop("plots_dir")

RAM_GUARD_ENABLED: bool = _cfg.pop("ram_guard_enabled")
RAM_SOFT_LIMIT_PERCENT: float = _cfg.pop("ram_soft_limit_percent")
RAM_HARD_LIMIT_PERCENT: float = _cfg.pop("ram_hard_limit_percent")
RAM_THROTTLE_SLEEP_SEC: float = _cfg.pop("ram_throttle_sleep_sec")
RAM_CHECK_EVERY_N_RECORDINGS: int = _cfg.pop("ram_check_every_n_recordings")

if _cfg:
    raise ValueError(f"Невідомі ключі в {CONFIG_PATH}: {sorted(_cfg)}")
del _cfg, _f
