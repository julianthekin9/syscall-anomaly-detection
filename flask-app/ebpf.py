#!/usr/bin/env python3

"""Сборщик системных вызовов контейнера через BCC (eBPF) 
Требования:
    sudo apt install bpfcc-tools python3-bpfcc linux-headers-$(uname -r)
    (root/CAP_SYS_ADMIN обязателен для загрузки eBPF-программы в ядро)

Запуск:
    # по имени/id контейнера — cgroup определится автоматически через docker inspect
    sudo python3 lidds_ebpf_collector_2021.py --container my_container --output out.sc

    # либо напрямую по PID (если контейнер не через docker, а просто процесс)
    sudo python3 lidds_ebpf_collector_2021.py --pid 12345 --output out.sc

    # без фильтра — писать вообще все syscall'ы в системе (для отладки)
    sudo python3 lidds_ebpf_collector_2021.py --output out.sc

ВАЖНО: этот скрипт пишет только сам .sc-файл трассы. JSON-метаданные записи
(<имя>.json — exploit/exploit_name/time.exploit[...].absolute и т.д.,
формат которых разбирает data2021.load_exploit_metadata_2021) этим
коллектором не генерируются — их нужно создавать отдельно вашим управляющим
скриптом атаки/сценария (он точно знает, был ли выполнен эксплойт и в какой
момент абсолютного времени).
"""

import argparse
import ctypes as ct
import os
import re
import subprocess
import sys
import time


def build_syscall_table() -> dict[int, str]:
    """Строит таблицу номер->имя для ТЕКУЩЕГО ядра/архитектуры.

    Порядок попыток:
      1) bcc.syscall.syscall_name — если установлен bcc, это самый надёжный
         источник (поддерживается проектом BCC, не наша самодеятельность).
      2) Разбор системного заголовка unistd_64.h — работает без bcc, даёт
         точную таблицу именно для этой машины.
      3) Пустая таблица (тогда все syscall'ы будут выводиться как syscall_N).
    """
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
    """Достаёт PID корневого процесса контейнера через docker inspect."""
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
    """Numeric cgroup id (cgroup v2) процесса — совпадает с тем, что вернёт
    bpf_get_current_cgroup_id() в eBPF-программе для процессов этого cgroup'а.
    """
    with open(f"/proc/{pid}/cgroup", encoding="utf-8") as f:
        # для cgroup v2 единственная строка вида "0::/path/to/cgroup"
        line = f.readline().strip()
    cgroup_path = line.split(":")[-1]
    full_path = f"/sys/fs/cgroup{cgroup_path}"
    return os.stat(full_path).st_ino

BPF_PROGRAM = r"""
#include <linux/sched.h>

struct event_t {
    u64 ts_ns;          // время события, наносекунды с момента загрузки BPF-программы (монотонное)
    u32 pid;             // tgid (то, что обычно называют PID процесса)
    u32 tid;             // id конкретного потока
    u32 uid;
    u32 cpu;
    char comm[TASK_COMM_LEN];
    s64 syscall_id;
    u8  direction;       // 0 = enter ('>'), 1 = exit ('<')
    s64 ret;             // валиден только при direction == 1
    u64 args[6];          // валидны только при direction == 0
};

BPF_PERF_OUTPUT(events);
BPF_ARRAY(cgroup_filter, u64, 1);

static inline bool should_trace() {
    u32 key = 0;
    u64 *target = cgroup_filter.lookup(&key);
    // если фильтр не задан (0) — трассируем вообще всё (режим отладки)
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
    if (!should_trace()) {
        return 0;
    }
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
    if (!should_trace()) {
        return 0;
    }
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
    """Должна побайтово совпадать со struct event_t в BPF_PROGRAM выше."""

    _fields_ = [
        ("ts_ns", ct.c_uint64),
        ("pid", ct.c_uint32),
        ("tid", ct.c_uint32),
        ("uid", ct.c_uint32),
        ("cpu", ct.c_uint32),
        ("comm", ct.c_char * 16),  # TASK_COMM_LEN
        ("syscall_id", ct.c_int64),
        ("direction", ct.c_uint8),
        ("ret", ct.c_int64),
        ("args", ct.c_uint64 * 6),
    ]


class Collector:
    """Держит состояние сборщика: открытый лог-файл, счётчик событий, таблицу syscall-ов.

    В отличие от 2019-версии, здесь НЕТ порядкового номера события в строке
    лога (2021-формат его не использует), а timestamp — абсолютный unix ns,
    а не "HH:MM:SS.ns".
    """

    def __init__(self, output_path: str, syscall_table: dict[int, str]) -> None:
        self.log = open(output_path, "a", encoding="utf-8")
        self.syscall_table = syscall_table
        self.event_counter = 0
        self.wall_clock_offset_ns = time.time_ns() - time.clock_gettime_ns(time.CLOCK_MONOTONIC)

    def to_absolute_unix_ns(self, ts_ns: int) -> int:
        """Переводит монотонный ts_ns события в абсолютный unix-timestamp
        (наносекунды) — та же система координат, что и у time.*.absolute в
        JSON-метаданных LID-DS 2021 (см. докстринг модуля)."""
        return ts_ns + self.wall_clock_offset_ns

    def handle_event(self, cpu: int, data, size: int) -> None:  # noqa: ARG002 (cpu/size — сигнатура BCC-колбэка)
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

        # формат: TIMESTAMP(ns) USER_ID PROCESS_ID PROCESS_NAME THREAD_ID SYSCALL_NAME DIRECTION [params...]
        line = (
            f"{absolute_ts_ns} {event.uid} {event.pid} "
            f"{process_name} {event.tid} {name} {direction_char} {params}\n"
        )
        self.log.write(line)

    def close(self) -> None:
        self.log.flush()
        self.log.close()


def start_collector(output_path: str, container: str | None, pid: int | None) -> None:
    if os.geteuid() != 0:
        print("Нужен root (или CAP_SYS_ADMIN) для загрузки eBPF-программы", file=sys.stderr)
        sys.exit(1)

    try:
        from bcc import BPF  # импорт здесь, чтобы --help работал и без установленного bcc
    except ImportError:
        print(
            "Модуль bcc не найден. Установите:\n"
            "  sudo apt install bpfcc-tools python3-bpfcc linux-headers-$(uname -r)",
            file=sys.stderr,
        )
        sys.exit(1)

    pid = pid if pid is not None else resolve_pid(container)
    cgroup_id = get_cgroup_id(pid) if pid is not None else 0
    if pid is not None:
        print(f"Фильтр по PID={pid}, cgroup_id={cgroup_id}")
    else:
        print("Фильтр не задан — трассируются syscall'ы ВСЕХ процессов в системе")

    syscall_table = build_syscall_table()
    print(f"Загружена таблица из {len(syscall_table)} syscall-ов")

    bpf = BPF(text=BPF_PROGRAM)
    bpf["cgroup_filter"][ct.c_int(0)] = ct.c_uint64(cgroup_id)

    collector = Collector(output_path, syscall_table)
    bpf["events"].open_perf_buffer(collector.handle_event)

    print(f"Пишу лог (формат LID-DS 2021) в {output_path}. Ctrl+C для остановки.")
    try:
        while True:
            bpf.perf_buffer_poll()
    except KeyboardInterrupt:
        pass
    finally:
        collector.close()
        print(f"Остановлено. Всего событий: {collector.event_counter}")

def run() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--container", help="Имя или id Docker-контейнера")
    parser.add_argument("--pid", type=int, help="PID процесса напрямую (если не через Docker)")
    parser.add_argument("--output", required=True, help="Путь к файлу лога (.sc)")
    args = parser.parse_args()

    start_collector(args.output, args.container, args.pid)


##############################################################################################

def collect_flask_dataset():

    CONTAINER = 'flask-app'

    NORMAL_DIR = './normal_logs'
    ABNORMAL_DIR = './abnormal_logs'

    NORMAL_PREFIX = 'normal'
    ABNORMAL_PREFIX = 'abnormal'

    FILE_SIZE_LIMIT = 10 * 1024 * 1024  # 10 MB


    def collect_class(normal: bool, files_count: int) -> None:

        if normal:
            dir = NORMAL_DIR
            prefix = NORMAL_PREFIX
        else:
            dir = ABNORMAL_DIR
            prefix = ABNORMAL_PREFIX

        os.makedirs(dir, exist_ok=True)

        try:
            for i in range(files_count):
                output_file = f"{dir}/{prefix}_{i}.sc"
                print(f"Пишу лог в {output_file}. Ctrl+C для остановки.")

                collector = Collector(output_file, syscall_table)
                state["collector"] = collector

                while os.path.getsize(output_file) < FILE_SIZE_LIMIT:
                    bpf.perf_buffer_poll(timeout=100)

                collector.close()
                print(f"Готово: {output_file}, событий: {collector.event_counter}")
        except KeyboardInterrupt:
            collector = state["collector"]
            if collector is not None:
                collector.close()
            print("Прервано пользователем")

    if os.geteuid() != 0:
        print("Нужен root (или CAP_SYS_ADMIN) для загрузки eBPF-программы", file=sys.stderr)
        sys.exit(1)

    try:
        from bcc import BPF
    except ImportError:
        print(
            "Модуль bcc не найден. Установите:\n"
            "  sudo apt install bpfcc-tools python3-bpfcc linux-headers-$(uname -r)",
            file=sys.stderr,
        )
        sys.exit(1)

    pid = resolve_pid(CONTAINER)
    cgroup_id = get_cgroup_id(pid) if pid is not None else 0
    if pid is not None:
        print(f"Фильтр по PID={pid}, cgroup_id={cgroup_id}")
    else:
        print("Фильтр не задан — трассируются syscall'ы ВСЕХ процессов в системе")

    syscall_table = build_syscall_table()
    print(f"Загружена таблица из {len(syscall_table)} syscall-ов")

    bpf = BPF(text=BPF_PROGRAM)
    bpf["cgroup_filter"][ct.c_int(0)] = ct.c_uint64(cgroup_id)

    state: dict[str, Collector | None] = {"collector": None}

    def dispatch(cpu, data, size):
        collector = state["collector"]
        if collector is not None:
            collector.handle_event(cpu, data, size)

    bpf["events"].open_perf_buffer(dispatch)

    collect_class(normal=True, files_count=100)
    collect_class(normal=False, files_count=100)

if __name__ == "__main__":
    collect_flask_dataset()