"""
Проба: детекция аномалий В РЕАЛЬНОМ ВРЕМЕНИ поверх ebpf.py — без записи на
диск и последующего чтения файла. syscall-события из BPF perf-buffer
попадают напрямую в модель через скользящее окно.

Не изменяет ebpf.py / data.py / model.py / predict.py — только импортирует
их. Единственная тонкость: EbpfSession.collect_to() создаёт СВОЙ
ebpf.Collector (пишущий в файл с блочной буферизацией — tail -f такого
файла не даёт настоящего realtime). Поэтому вместо collect_to() этот
скрипт напрямую подключает свой (in-memory) коллектор в тот же hook-point,
которым collect_to() пользуется внутри (`session._current_collector` /
`session._lock`, под тем же локом). Дублируется единственное: способ
превратить один ctypes-Event в ParsedLine (timestamp/process/syscall/
direction/arg_count) — он зеркалит ebpf.Collector.handle_event построчно
(включая то, что arg_count всегда 6 на sys_enter и 1 на sys_exit — это
жёстко зашито в BPF_PROGRAM/Collector, см. комментарий у ARGS_ON_*).
Сама кодировка признаков (vocab, arg_count-бакетизация) не дублируется —
используется data.encode_line() как есть.

Usage:
    sudo python realtime_detect.py --service FLASK --container my-flask-app
    sudo python realtime_detect.py --service FLASK --container my-flask-app --duration 120 --scan-interval 0.5
"""

import argparse
import csv
import ctypes as ct
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import torch

import config
from data import ParsedLine, encode_line
from  flask_app.ebpf import Event, EbpfSession, syscall_name
from model import compute_step_scores, aggregate_window_scores
from predict import load_model
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Жёстко зашито в ebpf.BPF_PROGRAM / ebpf.Collector.handle_event: на
# sys_enter пишется 6 полей "argN=0x..", на sys_exit — одно "res=..".
# Если формат строки в ebpf.py изменится — поправить и здесь.
ARGS_ON_ENTER = 6
ARGS_ON_EXIT = 1



class RealtimeCollector:
    """Duck-typed под интерфейс, который ждёт ebpf.EbpfSession.dispatch:
    объект с методом handle_event(cpu, data, size). Вместо файла кладёт
    закодированные строки в потокобезопасный кольцевой буфер для модели.
    """

    def __init__(self, syscall_table: dict[int, str], vocabs: dict[str, dict[str, int]], buffer_size: int) -> None:
        self.syscall_table = syscall_table
        self.vocabs = vocabs
        # то же самое вычисление, что в ebpf.Collector.__init__ — нужно,
        # чтобы ts_ns из BPF (CLOCK_MONOTONIC) перевести в абсолютные unix ns
        self.wall_clock_offset_ns = time.time_ns() - time.clock_gettime_ns(time.CLOCK_MONOTONIC)
        self.event_counter = 0
        self.lock = threading.Lock()
        # каждый элемент: (encoded_row: list[int], timestamp_sec: float)
        self.buffer: deque[tuple[list[int], float]] = deque(maxlen=buffer_size)

    def handle_event(self, cpu: int, data, size: int) -> None:  # noqa: ARG002
        event = ct.cast(data, ct.POINTER(Event)).contents
        self.event_counter += 1

        syscall = syscall_name(self.syscall_table, event.syscall_id)
        process_name = event.comm.decode("utf-8", errors="replace")
        is_enter = event.direction == 0
        direction = ">" if is_enter else "<"
        arg_count = ARGS_ON_ENTER if is_enter else ARGS_ON_EXIT
        timestamp_sec = (event.ts_ns + self.wall_clock_offset_ns) / 1e9

        parsed = ParsedLine(
            timestamp=timestamp_sec,
            syscall=syscall,
            process_name=process_name,
            direction=direction,
            arg_count=arg_count,
        )
        if parsed.syscall == "switch":
            return  # как и read_recording() в data.py, switch-события выбрасываются

        row = encode_line(self.vocabs, parsed)
        with self.lock:
            self.buffer.append((row, timestamp_sec))

    def snapshot_tail(self, n: int) -> tuple[list[list[int]], list[float]] | None:
        """Последние n событий буфера, если их достаточно накопилось."""
        with self.lock:
            if len(self.buffer) < n:
                return None
            tail = list(self.buffer)[-n:]
        rows = [r for r, _ in tail]
        timestamps = [t for _, t in tail]
        return rows, timestamps


def attach_collector(session: EbpfSession, collector: RealtimeCollector) -> None:
    """Аналог того, что EbpfSession.collect_to() делает внутри себя, но с
    нашим in-memory коллектором вместо ebpf.Collector (публичного способа
    подставить свой коллектор в EbpfSession сейчас нет)."""
    with session._lock:  # noqa: SLF001
        session._current_collector = collector  # noqa: SLF001


def detach_collector(session: EbpfSession) -> None:
    with session._lock:  # noqa: SLF001
        session._current_collector = None  # noqa: SLF001


def score_window(model, rows: list[list[int]], device: torch.device) -> float:
    """rows: seq_len+1 закодированных событий подряд. Возвращает NLL окна
    (та же формула, что при обучении/оценке: compute_step_scores +
    аггрегация из чекпоинта)."""
    x = torch.tensor(rows[:-1], dtype=torch.long, device=device).unsqueeze(0)  # [1, seq_len, feat]
    y_syscall = torch.tensor([r[0] for r in rows[1:]], dtype=torch.long, device=device)
    y_process = torch.tensor([r[1] for r in rows[1:]], dtype=torch.long, device=device)
    y = torch.stack([y_syscall, y_process], dim=-1).unsqueeze(0)  # [1, seq_len, 2]
    with torch.no_grad():
        logits_syscall = model(x)
        step_scores = compute_step_scores(logits_syscall, y)
    return step_scores  # [1, seq_len], аггрегируем снаружи (нужен window_agg из чекпоинта)

def plot_file_timeline(
    filename: str,
    window_end_ts: np.ndarray,
    scores: np.ndarray,
    attack_start_sec: float | None,
    threshold: float,
    out_path: Path,
) -> None:
    if len(window_end_ts) == 0:
        return

    t0 = window_end_ts.min()
    rel_t = window_end_ts - t0
    is_attack_window = (
        window_end_ts >= attack_start_sec if attack_start_sec is not None else np.zeros_like(window_end_ts, dtype=bool)
    )

    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(rel_t, scores, "-", color="#888888", linewidth=1, zorder=1)
    ax.scatter(
        rel_t[~is_attack_window], scores[~is_attack_window],
        color="#2563eb", label="окно: normal (по времени)", s=18, zorder=2,
    )
    if is_attack_window.any():
        ax.scatter(
            rel_t[is_attack_window], scores[is_attack_window],
            color="#dc2626", label="окно: attack (по времени)", s=18, zorder=2,
        )

    ax.axhline(threshold, color="#16a34a", linestyle="--", linewidth=1.2, label=f"threshold = {threshold:.4f}")
    if attack_start_sec is not None:
        ax.axvline(attack_start_sec - t0, color="#dc2626", linestyle=":", linewidth=1.5, label="начало атаки (info.json)")

    ax.set_xlabel("время от начала записи, с")
    ax.set_ylabel("NLL (anomaly score)")
    ax.set_title(f"{filename} — NLL по временным меткам лога")
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--service", required=True, help="Имя сервиса (models/<service>.pt)")
    parser.add_argument("--container", default=None, help="Имя/ID Docker-контейнера для трассировки")
    parser.add_argument("--pid", type=int, default=None, help="Альтернатива --container: конкретный PID")
    parser.add_argument("--checkpoint", default=None, help="Явный путь к .pt (по умолчанию — config.MODEL_DIR/<service>.pt)")
    parser.add_argument("--scan-interval", type=float, default=1.0, help="Пауза между проверками окна, сек")
    parser.add_argument("--duration", type=float, default=0.0, help="Остановиться через N секунд (0 = до Ctrl+C)")
    parser.add_argument("--out-dir", default="./realtime_runs", help="Куда сохранять CSV/график по завершении")
    parser.add_argument("--attack-marker", type=float, default=None,
                         help="Для тестовых прогонов: секунды от старта, когда была инициирована атака "
                              "(рисуется вертикальной линией на итоговом графике, как в probe_eval)")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if args.checkpoint:
        checkpoint = torch.load(args.checkpoint, map_location=device)
        from model import SyscallLSTM
        model = SyscallLSTM.from_checkpoint(checkpoint, device)
        model.eval()
    else:
        model, checkpoint = load_model(args.service, device)

    vocabs = checkpoint["vocabs"]
    seq_len = checkpoint["seq_len"]
    window_agg = checkpoint["window_agg"]
    window_agg_quantile = checkpoint["window_agg_quantile"]
    threshold = checkpoint["threshold"]
    needed = seq_len + 1

    print(f"[{args.service}] device={device} seq_len={seq_len} window_agg={window_agg} threshold={threshold:.4f}")

    session = EbpfSession(container=args.container, pid=args.pid)
    collector = RealtimeCollector(session.syscall_table, vocabs, buffer_size=max(needed * 20, 4096))
    attach_collector(session, collector)

    history_ts: list[float] = []
    history_scores: list[float] = []
    history_alert: list[bool] = []
    last_scored_event_count = -1
    run_start = time.time()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("Слежу за syscall-потоком в реальном времени (Ctrl+C — остановить)...")
    try:
        while True:
            time.sleep(args.scan_interval)

            if collector.event_counter != last_scored_event_count:
                snap = collector.snapshot_tail(needed)
                if snap is not None:
                    rows, timestamps = snap
                    step_scores = score_window(model, rows, device)
                    score = aggregate_window_scores(
                        step_scores, window_agg=window_agg, window_agg_quantile=window_agg_quantile
                    ).item()
                    is_alert = score > threshold
                    window_ts = timestamps[-1]

                    history_ts.append(window_ts)
                    history_scores.append(score)
                    history_alert.append(is_alert)
                    last_scored_event_count = collector.event_counter

                    ts_label = datetime.fromtimestamp(window_ts).strftime("%H:%M:%S")
                    marker = "  <-- ALERT" if is_alert else ""
                    print(f"[{ts_label}] events={collector.event_counter:>8}  nll={score:.4f}{marker}")

            if args.duration and (time.time() - run_start) >= args.duration:
                print(f"Достигнут --duration={args.duration}с — останавливаюсь")
                break
    except KeyboardInterrupt:
        print("\nОстановлено пользователем (Ctrl+C)")
    finally:
        detach_collector(session)
        session.close()

    if not history_scores:
        print("Не набралось ни одного полного окна (seq_len+1 событий) — нечего сохранять")
        return

    csv_path = out_dir / f"{args.service}_{run_id}_scores.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_unix", "nll", "alert"])
        for ts, score, alert in zip(history_ts, history_scores, history_alert):
            writer.writerow([f"{ts:.6f}", f"{score:.6f}", int(alert)])
    print(f"История окон сохранена: {csv_path}")

    import numpy as np
    window_end_ts = np.array(history_ts, dtype=np.float64)
    scores = np.array(history_scores, dtype=np.float64)
    attack_start_sec = (window_end_ts[0] + args.attack_marker) if args.attack_marker is not None else None
    plot_path = out_dir / f"{args.service}_{run_id}_nll_timeline.png"
    plot_file_timeline(
        f"{args.service} realtime ({run_id})", window_end_ts, scores, attack_start_sec, threshold, plot_path
    )
    print(f"График сохранён: {plot_path}")

    n_alerts = sum(history_alert)
    print(f"Итого: {len(history_scores)} окон, {n_alerts} алертов ({100 * n_alerts / len(history_scores):.1f}%)")


if __name__ == "__main__":
    main()
