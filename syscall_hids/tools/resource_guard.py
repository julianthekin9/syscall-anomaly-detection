import gc
import logging
import os
import time

import psutil

_process = psutil.Process(os.getpid())

# The only allowed module-level state in the package. check_ram is called deep in the data layer,
# so settings are set once via configure() at the entry point (run_train.run,
# eval_recordings.main) instead of being passed through every function. The guard is off until configure().
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
    """Raised in advance, before the OOM killer kills the process."""


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
            f"RAM usage at {pct:.1f}% (hard limit ram_hard_limit_percent="
            f"{_hard_limit_percent}%), process RSS={process_rss_gb():.2f} GB, "
            f"context: {context or '?'}."
        )

    if pct >= _soft_limit_percent:
        logging.warning(
            f"[resource_guard] WARNING: RAM {pct:.1f}% "
            f"(soft limit {_soft_limit_percent}%), "
            f"process RSS={process_rss_gb():.2f} GB, context: {context or '?'}: "
            f"gc.collect() + pause {_throttle_sleep_sec}s"
        )
        gc.collect()
        time.sleep(_throttle_sleep_sec)
