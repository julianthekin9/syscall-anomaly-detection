from dataclasses import dataclass, field
from threading import Thread
from time import time as now
from typing import Callable

from normal_traffic import run_normal_traffic
from abnormal_traffic import command_execution, network, process_info


@dataclass
class TrafficSpec:
    """Описание одного вида трафика: что запускать, сколько инстансов,
    сколько длится. target принимает duration первым позиционным
    аргументом и сам возвращается по истечении этого времени."""
    name: str
    target: Callable[..., None]
    duration: float
    instance_count: int = 1
    extra_args: tuple = field(default_factory=tuple)


class TrafficRunner:
    """Запускает произвольный набор TrafficSpec параллельно и ждёт
    завершения всех (каждый target сам укладывается в свой duration)."""

    def __init__(self, specs: list[TrafficSpec]):
        self._specs = specs
        self._threads: list[Thread] = []

    def _make_thread(self, spec: TrafficSpec, index: int) -> Thread:
        def wrapper():
            spec.target(spec.duration, *spec.extra_args)

        return Thread(target=wrapper, daemon=True, name=f"{spec.name}#{index}")

    def start(self) -> None:
        for spec in self._specs:
            for i in range(spec.instance_count):
                t = self._make_thread(spec, i)
                self._threads.append(t)
                t.start()
                print(f"Запущен: {spec.name} #{i} (duration={spec.duration}с)")

    def join(self) -> None:
        max_duration = max((s.duration for s in self._specs), default=0)
        grace = max_duration + 10  # запас на текущий request(timeout=3) внутри последней сессии
        for t in self._threads:
            t.join(timeout=grace)
            if t.is_alive():
                print(f"ВНИМАНИЕ: поток {t.name} не завершился вовремя")

    def run(self) -> None:
        start = now()
        self.start()
        self.join()
        elapsed = now() - start
        print(f"Весь трафик завершён за {elapsed:.1f}с")


def normal(duration: float, instance_count: int = 1) -> TrafficSpec:
    return TrafficSpec("normal", run_normal_traffic, duration, instance_count)


def abnormal_command_execution(duration: float, instance_count: int = 1) -> TrafficSpec:
    return TrafficSpec("abnormal:command_execution", command_execution, duration, instance_count)


def abnormal_network(duration: float, instance_count: int = 1) -> TrafficSpec:
    return TrafficSpec("abnormal:network", network, duration, instance_count)


def abnormal_process_info(duration: float, instance_count: int = 1) -> TrafficSpec:
    return TrafficSpec("abnormal:process_info", process_info, duration, instance_count)