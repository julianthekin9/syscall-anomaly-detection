import gc
import os
import time

import psutil

_process = psutil.Process(os.getpid())

# Єдиний дозволений модульний стан пакета. check_ram викликається глибоко в шарі даних,
# тож налаштування задаються один раз через configure() у точці входу (run_train.run,
# eval_recordings.main), а не протягуються через усі функції. До configure() охорона вимкнена.
_enabled = False
_soft_limit_percent = 100.0
_hard_limit_percent = 100.0
_throttle_sleep_sec = 0.0


def configure(enabled: bool, soft_limit_percent: float, hard_limit_percent: float, throttle_sleep_sec: float) -> None:
    global _enabled, _soft_limit_percent, _hard_limit_percent, _throttle_sleep_sec
    _enabled = enabled
    _soft_limit_percent = soft_limit_percent
    _hard_limit_percent = hard_limit_percent
    _throttle_sleep_sec = throttle_sleep_sec


class RamLimitExceeded(MemoryError):
    """Поднимается заблаговременно, до того как систему прибьёт OOM killer."""


def ram_usage_percent() -> float:
    return psutil.virtual_memory().percent


def process_rss_gb() -> float:
    return _process.memory_info().rss / (1024**3)


def check_ram(context: str = "") -> None:
    if not _enabled:
        return

    pct = ram_usage_percent()

    if pct >= _hard_limit_percent:
        raise RamLimitExceeded(
            f"RAM занята на {pct:.1f}% (жёсткий лимит ram_hard_limit_percent="
            f"{_hard_limit_percent}%), RSS процесса={process_rss_gb():.2f} GB, "
            f"контекст: {context or '?'}."
        )

    if pct >= _soft_limit_percent:
        print(
            f"[resource_guard] ВНИМАНИЕ: RAM {pct:.1f}% "
            f"(мягкий лимит {_soft_limit_percent}%), "
            f"RSS процесса={process_rss_gb():.2f} GB, контекст: {context or '?'} — "
            f"gc.collect() + пауза {_throttle_sleep_sec}s"
        )
        gc.collect()
        time.sleep(_throttle_sleep_sec)
