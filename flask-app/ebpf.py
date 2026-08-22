#!/usr/bin/env python3
"""Переиспользуемая eBPF-сессия: BPF грузится в ядро один раз, а конкретный
Collector (normal / abnormal / любой другой файл) подставляется на лету через
state["collector"], без повторной загрузки eBPF-программы между фазами.

Это рефактор lidds_ebpf_collector_2021.py: вся логика build_syscall_table /
resolve_pid / get_cgroup_id / BPF_PROGRAM / Event / Collector скопирована без
изменений (только оттуда убран collect-in-loop код, который тут не нужен).
"""

import ctypes as ct
import os
import re
import subprocess
import sys
import threading
import time
from contextlib import contextmanager

from bcc import BPF

# --- всё, что не менялось относительно исходного ebpf.py ---

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
    u32 pid;
    u32 tid;
    u32 uid;
    u32 cpu;
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
    u64 pid_tgid = bpf_get_current_pid_tgid();
    event->tid = pid_tgid & 0xFFFFFFFF;
    event->pid = pid_tgid >> 32;
    event->uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    event->cpu = bpf_get_smp_processor_id();
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
        ("pid", ct.c_uint32),
        ("tid", ct.c_uint32),
        ("uid", ct.c_uint32),
        ("cpu", ct.c_uint32),
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
            f"{absolute_ts_ns} {event.uid} {event.pid} "
            f"{process_name} {event.tid} {name} {direction_char} {params}\n"
        )
        self.log.write(line)

    def close(self) -> None:
        self.log.flush()
        self.log.close()


# --- новое: сессия с состоянием, живущая дольше одного файла ---

class EbpfSession:
    """Грузит eBPF-программу один раз и держит её всё время жизни объекта.
    Конкретный Collector подставляется через collect_to() на время одной фазы
    (normal / abnormal / что угодно), опрос perf buffer крутится в фоновом
    потоке непрерывно.
    """

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

        self._current_collector: Collector | None = None
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
        """Все syscall-события текущего cgroup'а на время `with`-блока
        пишутся в output_path. Один Collector — на один вызов."""
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

    def refresh_cgroup(self, container: str) -> None:
        """Перечитать PID/cgroup контейнера — вызывай, если контейнер мог
        перезапуститься между фазами (иначе фильтр будет указывать на
        мёртвый cgroup и новые события молча не попадут в лог)."""
        self.pid = resolve_pid(container)
        self.cgroup_id = get_cgroup_id(self.pid) if self.pid is not None else 0
        self.bpf["cgroup_filter"][ct.c_int(0)] = ct.c_uint64(self.cgroup_id)
        print(f"cgroup обновлён: PID={self.pid}, cgroup_id={self.cgroup_id}")

    def close(self) -> None:
        self._stop_event.set()
        self._poll_thread.join(timeout=2)