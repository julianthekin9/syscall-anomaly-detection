"""Формат рядка трасу (як пише eBPF-колектор і конвертер LID-DS): "ts_ns process syscall dir params...".

Це контракт із джерелами даних, а не параметри експерименту: зміна формату події
eBPF (event_t / Event / Collector) вимагає синхронно оновити ці індекси.
"""

TIME_COLUMN_INDEX = 0
PROCESS_NAME_COLUMN_INDEX = 1
SYSCALL_COLUMN_INDEX = 2
DIRECTION_COLUMN_INDEX = 3
PARAMS_BEGIN_INDEX = 4  # всё после этого индекса — параметры syscall'а
MIN_RAW_FIELDS = 4

RECORDING_EXTENSION = ".sc"
