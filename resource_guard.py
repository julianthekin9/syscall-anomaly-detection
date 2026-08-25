import gc
import os
import time

import psutil

import config

_process = psutil.Process(os.getpid())


class RamLimitExceeded(MemoryError):
    """Поднимается заблаговременно, до того как систему прибьёт OOM killer."""


def ram_usage_percent() -> float:
    return psutil.virtual_memory().percent


def process_rss_gb() -> float:
    return _process.memory_info().rss / (1024**3)


def check_ram(context: str = "") -> None:
    if not config.RAM_GUARD_ENABLED:
        return

    pct = ram_usage_percent()

    if pct >= config.RAM_HARD_LIMIT_PERCENT:
        raise RamLimitExceeded(
            f"RAM занята на {pct:.1f}% (жёсткий лимит config.RAM_HARD_LIMIT_PERCENT="
            f"{config.RAM_HARD_LIMIT_PERCENT}%), RSS процесса={process_rss_gb():.2f} GB, "
            f"контекст: {context or '?'}."
        )

    if pct >= config.RAM_SOFT_LIMIT_PERCENT:
        print(
            f"[resource_guard] ВНИМАНИЕ: RAM {pct:.1f}% "
            f"(мягкий лимит {config.RAM_SOFT_LIMIT_PERCENT}%), "
            f"RSS процесса={process_rss_gb():.2f} GB, контекст: {context or '?'} — "
            f"gc.collect() + пауза {config.RAM_THROTTLE_SLEEP_SEC}s"
        )
        gc.collect()
        time.sleep(config.RAM_THROTTLE_SLEEP_SEC)
