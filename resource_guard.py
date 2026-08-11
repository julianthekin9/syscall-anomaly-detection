"""Мониторинг потребления RAM во время построения датасета и обучения.

ЗАЧЕМ: OOM killer в Linux присылает процессу SIGKILL — без исключения, без
трейсбека, без шанса что-то сделать (сохранить чекпоинт, освободить память,
хотя бы вывести внятное сообщение). Со стороны это выглядит как "всё просто
взяло и вылетело". Этот модуль даёт возможность отреагировать РАНЬШЕ:

- мягкий порог (config.RAM_SOFT_LIMIT_PERCENT) — gc.collect() + короткая
  пауза (дать ОС/аллокатору шанс подобрать память) + предупреждение в лог.
  Работа продолжается.
- жёсткий порог (config.RAM_HARD_LIMIT_PERCENT) — контролируемая остановка:
  поднимается RamLimitExceeded с диагностикой (сколько занято RAM, RSS
  этого процесса, где именно это произошло) — вместо молчаливого SIGKILL.

ВАЖНО: это СТРАХОВКА, а не решение проблемы по существу. Основное снижение
потребления памяти — в data.py (окна хранятся как numpy-массивы int32/int64,
а не как вложенные списки Python-объектов, это в разы компактнее). Если вы
регулярно упираетесь в HARD_LIMIT — сначала попробуйте уменьшить SEQ_LEN,
BATCH_SIZE или обрабатывать сервисы по одному (python train.py --service X
в отдельных процессах), а не просто поднимать лимиты.
"""

import gc
import os
import time

import psutil

import config

_process = psutil.Process(os.getpid())


class RamLimitExceeded(MemoryError):
    """Поднимается заблаговременно, до того как систему прибьёт OOM killer."""


def ram_usage_percent() -> float:
    """Доля занятой RAM ВСЕЙ системы (не только этого процесса) в процентах.
    OOM killer в Linux обычно реагирует на память системы/cgroup целиком, а
    не только на RSS одного процесса — поэтому это более надёжный сигнал,
    чем process_rss_gb() в одиночку."""
    return psutil.virtual_memory().percent


def process_rss_gb() -> float:
    """RSS (реально занятая физическая память) текущего процесса, ГБ."""
    return _process.memory_info().rss / (1024**3)


def check_ram(context: str = "") -> None:
    """Вызывать в "горячих" местах: после обработки очередной записи/пачки
    записей при построении последовательностей, в конце каждой эпохи и т.п.

    Ничего не делает, если config.RAM_GUARD_ENABLED=False.
    """
    if not config.RAM_GUARD_ENABLED:
        return

    pct = ram_usage_percent()

    if pct >= config.RAM_HARD_LIMIT_PERCENT:
        raise RamLimitExceeded(
            f"RAM занята на {pct:.1f}% (жёсткий лимит config.RAM_HARD_LIMIT_PERCENT="
            f"{config.RAM_HARD_LIMIT_PERCENT}%), RSS процесса={process_rss_gb():.2f} GB, "
            f"контекст: {context or '?'}. Останавливаюсь контролируемо, ДО того как это "
            f"сделал бы OOM killer. Варианты: уменьшить config.SEQ_LEN/BATCH_SIZE, "
            f"обрабатывать сервисы по одному (--service), увеличить config.SEQ_STEP "
            f"(меньше перекрытия окон = меньше дублирования данных в памяти)."
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
