from dataclasses import dataclass, field
from threading import Barrier, Thread
from time import sleep, time_ns
from typing import Callable

from normal_traffic import run_normal_traffic
from abnormal_traffic import command_execution, network, process_info


@dataclass
class TrafficSpec:
    """Описание одного вида трафика."""
    name: str
    target: Callable[..., None]
    duration: float
    delay: float = 0
    instance_count: int = 1
    extra_args: tuple = field(default_factory=tuple)


class TrafficRunner:
    """Запускает произвольный набор TrafficSpec.

    Все потоки запускаются сразу.
    Каждый сценарий ждёт свой delay.
    После delay экземпляры одного сценария синхронизируются
    через Barrier и одновременно начинают выполнение target.

    run() возвращает фактические timestamps начала сценариев
    в Unix time наносекундах.
    """

    def __init__(self, specs: list[TrafficSpec]):
        self._specs = specs
        self._threads: list[Thread] = []
        self._start_times: dict[str, int] = {}

    def _make_thread(
        self,
        spec: TrafficSpec,
        index: int,
        barrier: Barrier,
    ) -> Thread:

        def wrapper():
            sleep(spec.delay)

            barrier.wait()

            # Unix timestamp в наносекундах.
            if spec.name not in self._start_times:
                self._start_times[spec.name] = time_ns()

            print(
                f"Запущен: {spec.name} #{index} "
                f"(duration={spec.duration}с)"
            )

            spec.target(spec.duration, *spec.extra_args)

        return Thread(
            target=wrapper,
            daemon=True,
            name=f"{spec.name}#{index}",
        )

    def start(self) -> None:
        """Создаёт и запускает все потоки."""

        for spec in self._specs:
            barrier = Barrier(spec.instance_count)

            for i in range(spec.instance_count):
                thread = self._make_thread(
                    spec,
                    i,
                    barrier,
                )

                self._threads.append(thread)
                thread.start()

                print(
                    f"Подготовлен: {spec.name} #{i} "
                    f"(delay={spec.delay}с, "
                    f"duration={spec.duration}с)"
                )

    def join(self) -> None:
        """Ждёт завершения всех потоков."""

        max_duration = max(
            (
                spec.delay + spec.duration
                for spec in self._specs
            ),
            default=0,
        )

        grace = max_duration + 10

        for thread in self._threads:
            thread.join(timeout=grace)

            if thread.is_alive():
                print(
                    f"ВНИМАНИЕ: поток {thread.name} "
                    f"не завершился вовремя"
                )

    def run(self) -> dict[str, int]:
        """Запускает трафик, ждёт завершения и возвращает timestamps."""

        start = time_ns()

        self.start()
        self.join()

        elapsed = (time_ns() - start) / 1_000_000_000

        print(f"Весь трафик завершён за {elapsed:.1f}с")

        return self._start_times


def normal(
    duration: float,
    instance_count: int = 1,
    delay: float = 0,
) -> TrafficSpec:
    return TrafficSpec(
        "normal",
        run_normal_traffic,
        duration,
        delay,
        instance_count,
    )


def abnormal_command_execution(
    duration: float,
    instance_count: int = 1,
    delay: float = 0,
) -> TrafficSpec:
    return TrafficSpec(
        "abnormal:command_execution",
        command_execution,
        duration,
        delay,
        instance_count,
    )


def abnormal_network(
    duration: float,
    instance_count: int = 1,
    delay: float = 0,
) -> TrafficSpec:
    return TrafficSpec(
        "abnormal:network",
        network,
        duration,
        delay,
        instance_count,
    )


def abnormal_process_info(
    duration: float,
    instance_count: int = 1,
    delay: float = 0,
) -> TrafficSpec:
    return TrafficSpec(
        "abnormal:process_info",
        process_info,
        duration,
        delay,
        instance_count,
    )

if __name__ == '__main__':
    TrafficRunner([
        normal(duration=50, instance_count=1, delay=0),
        abnormal_command_execution(duration=30, delay=20),
        abnormal_network(duration=30, delay=20),
        abnormal_process_info(duration=30, delay=20),
    ]).run()