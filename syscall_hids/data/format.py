"""Trace line format (as written by the eBPF collector and the LID-DS converter): "ts_ns process syscall dir params...".

This is a contract with the data sources, not experiment parameters: changing the eBPF
event format (event_t / Event / Collector) requires updating these indices in sync.
"""

TIME_COLUMN_INDEX = 0
PROCESS_NAME_COLUMN_INDEX = 1
SYSCALL_COLUMN_INDEX = 2
DIRECTION_COLUMN_INDEX = 3
PARAMS_BEGIN_INDEX = 4  # everything after this index is syscall parameters
MIN_RAW_FIELDS = 4

RECORDING_EXTENSION = ".sc"
