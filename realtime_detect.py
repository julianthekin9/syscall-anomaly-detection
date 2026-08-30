"""
Usage:
    sudo python realtime_detect.py --service FLASK --container flask-app
    sudo python realtime_detect.py --service FLASK --container flask-app --duration 120 --scan-interval 0.5
"""

import argparse
import csv
import time
from datetime import datetime
from pathlib import Path

import torch

from data import ParsedLine, encode_line
from utils.ebpf import EbpfSession, RealTimeCollector
from model import compute_step_scores, aggregate_window_scores
from predict import load_model
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def encode_tail(vocabs: dict[str, dict[str, int]], raw_events) -> tuple[list[list[int]], list[float]]:
    rows: list[list[int]] = []
    timestamps: list[float] = []
    for raw in raw_events:
        parsed = ParsedLine(
            timestamp=raw.timestamp,
            syscall=raw.syscall,
            process_name=raw.process_name,
            direction=raw.direction,
            arg_count=raw.arg_count,
        )
        rows.append(encode_line(vocabs, parsed))
        timestamps.append(raw.timestamp)
    return rows, timestamps


def score_window(model, rows: list[list[int]], device: torch.device) -> float:
    x = torch.tensor(rows[:-1], dtype=torch.long, device=device).unsqueeze(0)  # [1, seq_len, feat]
    y = torch.tensor([r[0] for r in rows[1:]], dtype=torch.long, device=device).view(1, -1, 1)  # [1, seq_len, 1]
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

    ax.set_xlabel("Час від початку запису, с")
    ax.set_ylabel("NLL (anomaly score)")
    ax.set_title(f"{filename} — NLL по часовим меткам лога")
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--checkpoint", default=None, help="Явный путь к .pt (по умолчанию — config.MODEL_DIR/<service>.pt)")
    parser.add_argument("--scan-interval", type=float, default=1.0, help="Пауза между проверками окна, сек")
    parser.add_argument("--duration", type=float, default=0.0, help="Остановиться через N секунд (0 = до Ctrl+C)")
    parser.add_argument("--out-dir", default="./realtime_runs", help="Куда сохранять CSV/график по завершении")
    parser.add_argument("--attack-marker", type=float, default=None,
                         help="Для тестовых прогонов: секунды от старта, когда была инициирована атака "
                              "(рисуется вертикальной линией на итоговом графике, как в probe_eval)")
    args = parser.parse_args()

    CONTAINER = 'flask-app'
    SERVICE = 'FLASK'

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if args.checkpoint:
        checkpoint = torch.load(args.checkpoint, map_location=device)
        from model import SyscallLSTM
        model = SyscallLSTM.from_checkpoint(checkpoint, device)
        model.eval()
    else:
        model, checkpoint = load_model(SERVICE, device)

    vocabs = checkpoint["vocabs"]
    seq_len = checkpoint["seq_len"]
    window_agg = checkpoint["window_agg"]
    window_agg_quantile = checkpoint["window_agg_quantile"]
    threshold = checkpoint["threshold"]
    needed = seq_len + 1

    print(f"[{SERVICE}] device={device} seq_len={seq_len} window_agg={window_agg} threshold={threshold:.4f}")

    session = EbpfSession(container=CONTAINER)
    collector = RealTimeCollector(session.syscall_table, buffer_size=max(needed * 20, 4096))
    session.attach_collector(collector)

    history_ts: list[float] = []
    history_scores: list[float] = []
    history_alert: list[bool] = []
    last_scored_event_count = -1
    run_start = time.time()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("Слідкую за syscall-потоком в реальному часі (Ctrl+C — остановить)...")
    try:
        while True:
            time.sleep(args.scan_interval)

            if collector.event_counter != last_scored_event_count:
                raw_tail = collector.snapshot_tail(needed)
                if raw_tail is not None:
                    rows, timestamps = encode_tail(vocabs, raw_tail)
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
                print(f"Досягнуто --duration={args.duration}с — зупиняюсь.")
                break
    except KeyboardInterrupt:
        print("\nЗупинено користувачем (Ctrl+C)")
    finally:
        session.detach_collector()
        session.close()

    if not history_scores:
        print("Недостатньо подій для повного вікна.")
        return

    csv_path = out_dir / f"{SERVICE}_{run_id}_scores.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_unix", "nll", "alert"])
        for ts, score, alert in zip(history_ts, history_scores, history_alert):
            writer.writerow([f"{ts:.6f}", f"{score:.6f}", int(alert)])
    print(f"Історію вікон збережено: {csv_path}")

    window_end_ts = np.array(history_ts, dtype=np.float64)
    scores = np.array(history_scores, dtype=np.float64)
    attack_start_sec = (window_end_ts[0] + args.attack_marker) if args.attack_marker is not None else None
    plot_path = out_dir / f"{SERVICE}_{run_id}_nll_timeline.png"
    plot_file_timeline(
        f"{SERVICE} realtime ({run_id})", window_end_ts, scores, attack_start_sec, threshold, plot_path
    )
    print(f"Графік збережено: {plot_path}")

    n_alerts = sum(history_alert)
    print(f"Ітог: {len(history_scores)} вікон, {n_alerts} алертов ({100 * n_alerts / len(history_scores):.1f}%)")


if __name__ == "__main__":
    main()