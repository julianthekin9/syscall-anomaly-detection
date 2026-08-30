#!/usr/bin/env python3
import ctypes as ct
import os
import re
import subprocess
import sys
import threading
import time
from collections import deque, namedtuple
from contextlib import contextmanager

from bcc import BPF

def build_syscall_table() -> dict[int, str]:
    try:
        from bcc import syscall as bcc_syscall

        table: dict[int, str] = {}
        for number in range(550):
            name_bytes = bcc_syscall.syscall_name(number)
            if name_bytes and name_bytes != b"[unknown]":
                table[number] = name_bytes.decode("utf-8", errors="replace")
        if table:
            return table
    except ImportError:
        pass

    header_candidates = [
        "/usr/include/x86_64-linux-gnu/asm/unistd_64.h",
        "/usr/include/asm/unistd_64.h",
    ]
    pattern = re.compile(r"#define\s+__NR_(\w+)\s+(\d+)")
    table = {}
    for path in header_candidates:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                match = pattern.match(line.strip())
                if match:
                    name, number = match.group(1), int(match.group(2))
                    table[number] = name
        if table:
            break
    return table


def syscall_name(table: dict[int, str], number: int) -> str:
    return table.get(number, f"syscall_{number}")


def resolve_pid(container: str | None) -> int | None:
    if container is None:
        return None
    try:
        output = subprocess.check_output(
            ["docker", "inspect", "--format", "{{.State.Pid}}", container],
            text=True,
        ).strip()
        return int(output)
    except (subprocess.CalledProcessError, ValueError) as exc:
        print(f"Не удалось получить PID контейнера {container!r}: {exc}", file=sys.stderr)
        sys.exit(1)


def get_cgroup_id(pid: int) -> int:
    with open(f"/proc/{pid}/cgroup", encoding="utf-8") as f:
        line = f.readline().strip()
    cgroup_path = line.split(":")[-1]
    full_path = f"/sys/fs/cgroup{cgroup_path}"
    return os.stat(full_path).st_ino


BPF_PROGRAM = r"""
#include <linux/sched.h>

struct event_t {
    u64 ts_ns;
    char comm[TASK_COMM_LEN];
    s64 syscall_id;
    u8  direction;
    s64 ret;
    u64 args[6];
};

BPF_PERF_OUTPUT(events);
BPF_ARRAY(cgroup_filter, u64, 1);

static inline bool should_trace() {
    u32 key = 0;
    u64 *target = cgroup_filter.lookup(&key);
    if (target == 0 || *target == 0) {
        return true;
    }
    return bpf_get_current_cgroup_id() == *target;
}

static inline void fill_common(struct event_t *event) {
    event->ts_ns = bpf_ktime_get_ns();
    bpf_get_current_comm(&event->comm, sizeof(event->comm));
}

TRACEPOINT_PROBE(raw_syscalls, sys_enter) {
    if (!should_trace()) { return 0; }
    struct event_t event = {};
    fill_common(&event);
    event.syscall_id = args->id;
    event.direction = 0;
    #pragma unroll
    for (int i = 0; i < 6; i++) {
        event.args[i] = args->args[i];
    }
    events.perf_submit(args, &event, sizeof(event));
    return 0;
}

TRACEPOINT_PROBE(raw_syscalls, sys_exit) {
    if (!should_trace()) { return 0; }
    struct event_t event = {};
    fill_common(&event);
    event.syscall_id = args->id;
    event.direction = 1;
    event.ret = args->ret;
    events.perf_submit(args, &event, sizeof(event));
    return 0;
}
"""


class Event(ct.Structure):
    _fields_ = [
        ("ts_ns", ct.c_uint64),
        ("comm", ct.c_char * 16),
        ("syscall_id", ct.c_int64),
        ("direction", ct.c_uint8),
        ("ret", ct.c_int64),
        ("args", ct.c_uint64 * 6),
    ]


class Collector:
    def __init__(self, output_path: str, syscall_table: dict[int, str]) -> None:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        self.log = open(output_path, "a", encoding="utf-8")
        self.syscall_table = syscall_table
        self.event_counter = 0
        self.wall_clock_offset_ns = time.time_ns() - time.clock_gettime_ns(time.CLOCK_MONOTONIC)

    def to_absolute_unix_ns(self, ts_ns: int) -> int:
        return ts_ns + self.wall_clock_offset_ns

    def handle_event(self, cpu: int, data, size: int) -> None:  # noqa: ARG002
        event = ct.cast(data, ct.POINTER(Event)).contents
        self.event_counter += 1

        name = syscall_name(self.syscall_table, event.syscall_id)
        process_name = event.comm.decode("utf-8", errors="replace")
        direction_char = ">" if event.direction == 0 else "<"
        absolute_ts_ns = self.to_absolute_unix_ns(event.ts_ns)

        if event.direction == 0:
            params = " ".join(f"arg{i}=0x{event.args[i]:x}" for i in range(6))
        else:
            params = f"res={event.ret}"

        line = (
            f"{absolute_ts_ns} {process_name} {name} {direction_char} {params}\n"
        )
        self.log.write(line)

    def close(self) -> None:
        self.log.flush()
        self.log.close()


RawEvent = namedtuple("RawEvent", ["timestamp", "process_name", "syscall", "direction", "arg_count"])


class RealTimeCollector:
    def __init__(self, syscall_table: dict[int, str], buffer_size: int = 10_000) -> None:
        self.syscall_table = syscall_table
        self.wall_clock_offset_ns = time.time_ns() - time.clock_gettime_ns(time.CLOCK_MONOTONIC)
        self.event_counter = 0
        self._lock = threading.Lock()
        self._buffer: deque[RawEvent] = deque(maxlen=buffer_size)

    def to_absolute_unix_ns(self, ts_ns: int) -> int:
        return ts_ns + self.wall_clock_offset_ns

    def handle_event(self, cpu: int, data, size: int) -> None:  # noqa: ARG002
        event = ct.cast(data, ct.POINTER(Event)).contents
        self.event_counter += 1

        name = syscall_name(self.syscall_table, event.syscall_id)
        if name == "switch":
            return  # как и data.read_recording() при чтении .sc-файлов — эти события не участвуют в обучении/инференсе

        process_name = event.comm.decode("utf-8", errors="replace")
        is_enter = event.direction == 0
        direction = ">" if is_enter else "<"
        arg_count = 6 if is_enter else 1
        timestamp_sec = self.to_absolute_unix_ns(event.ts_ns) / 1e9

        raw = RawEvent(
            timestamp=timestamp_sec,
            process_name=process_name,
            syscall=name,
            direction=direction,
            arg_count=arg_count,
        )
        with self._lock:
            self._buffer.append(raw)

    def snapshot_tail(self, n: int) -> list[RawEvent] | None:
        """Последние n событий буфера, или None, если их пока меньше n."""
        with self._lock:
            if len(self._buffer) < n:
                return None
            return list(self._buffer)[-n:]

    def __len__(self) -> int:
        with self._lock:
            return len(self._buffer)

    def close(self) -> None:
        pass  # на диске ничего не открыто — метод для симметрии с Collector.close()


class EbpfSession:

    def __init__(self, container: str | None = None, pid: int | None = None) -> None:
        if os.geteuid() != 0:
            print("Нужен root (или CAP_SYS_ADMIN) для загрузки eBPF-программы", file=sys.stderr)
            sys.exit(1)

        self.pid = pid if pid is not None else resolve_pid(container)
        self.cgroup_id = get_cgroup_id(self.pid) if self.pid is not None else 0
        if self.pid is not None:
            print(f"Фильтр по PID={self.pid}, cgroup_id={self.cgroup_id}")
        else:
            print("Фильтр не задан — трассируются syscall'ы ВСЕХ процессов в системе")

        self.syscall_table = build_syscall_table()
        print(f"Загружена таблица из {len(self.syscall_table)} syscall-ов")

        self.bpf = BPF(text=BPF_PROGRAM)
        self.bpf["cgroup_filter"][ct.c_int(0)] = ct.c_uint64(self.cgroup_id)

        self._current_collector: Collector | RealTimeCollector | None = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

        def dispatch(cpu, data, size):
            with self._lock:
                collector = self._current_collector
            if collector is not None:
                collector.handle_event(cpu, data, size)

        self.bpf["events"].open_perf_buffer(dispatch)

        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

    def _poll_loop(self) -> None:
        while not self._stop_event.is_set():
            self.bpf.perf_buffer_poll(timeout=100)

    @contextmanager
    def collect_to(self, output_path: str):
        collector = Collector(output_path, self.syscall_table)
        with self._lock:
            self._current_collector = collector
        try:
            print(f"Пишу лог в {output_path}")
            yield collector
        finally:
            with self._lock:
                self._current_collector = None
            collector.close()
            print(f"Готово: {output_path}, событий: {collector.event_counter}")

    def attach_collector(self, collector: "Collector | RealTimeCollector") -> None:
        with self._lock:
            self._current_collector = collector

    def detach_collector(self) -> None:
        with self._lock:
            self._current_collector = None

    def refresh_cgroup(self, container: str) -> None:
        self.pid = resolve_pid(container)
        self.cgroup_id = get_cgroup_id(self.pid) if self.pid is not None else 0
        self.bpf["cgroup_filter"][ct.c_int(0)] = ct.c_uint64(self.cgroup_id)
        print(f"cgroup обновлён: PID={self.pid}, cgroup_id={self.cgroup_id}")

    def close(self) -> None:
        self._stop_event.set()
        self._poll_thread.join(timeout=2)