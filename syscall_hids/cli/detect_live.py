"""
Usage:
    sudo hids-detect --service FLASK --container flask-app
    sudo hids-detect --service FLASK --container flask-app --duration 120 --scan-interval 0.5
"""

import csv
import time
from datetime import datetime
from pathlib import Path

import torch

from syscall_hids.collectors.ebpf import EbpfSession, RealTimeCollector
from syscall_hids.data.parsing import ParsedLine
from syscall_hids.data.sequences import encode_line
from syscall_hids.modules.models import SyscallLSTM
from syscall_hids.modules.scoring import compute_step_scores, aggregate_window_scores
from syscall_hids.tools.arg_parser import build_detect_arg_parser
from syscall_hids.tools.arg_parser_tools import check_args
from syscall_hids.tools.checkpoint import checkpoint_features, load_model
from syscall_hids.tools.visualization import plot_file_timeline
import numpy as np


def encode_tail(
    vocabs: dict[str, dict[str, int]], raw_events, use_arg_count_feature: bool, arg_count_buckets: int
) -> tuple[list[list[int]], list[float]]:
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
        rows.append(encode_line(vocabs, parsed, use_arg_count_feature, arg_count_buckets))
        timestamps.append(raw.timestamp)
    return rows, timestamps


def score_window(model, rows: list[list[int]], device: torch.device) -> float:
    x = torch.tensor(rows[:-1], dtype=torch.long, device=device).unsqueeze(0)  # [1, seq_len, feat]
    y = torch.tensor([r[0] for r in rows[1:]], dtype=torch.long, device=device).view(1, -1, 1)  # [1, seq_len, 1]
    with torch.no_grad():
        logits_syscall = model(x)
        step_scores = compute_step_scores(logits_syscall, y)
    return step_scores  # [1, seq_len], аггрегируем снаружи (нужен window_agg из чекпоинта)


def main() -> None:
    parser = build_detect_arg_parser(description=__doc__)
    args, input_log_messages = check_args(parser.parse_args())
    for message, _ in input_log_messages:
        print(f"УВАГА: {message}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if args.checkpoint:
        checkpoint = torch.load(args.checkpoint, map_location=device)
        model = SyscallLSTM.from_checkpoint(checkpoint, device)
        model.eval()
    else:
        model, checkpoint = load_model(args.service, device, args.model_dir)

    vocabs = checkpoint["vocabs"]
    seq_len = checkpoint["seq_len"]
    window_agg = checkpoint["window_agg"]
    window_agg_quantile = checkpoint["window_agg_quantile"]
    threshold = checkpoint["threshold"]
    use_arg_count_feature, arg_count_buckets = checkpoint_features(checkpoint)
    needed = seq_len + 1

    print(f"[{args.service}] device={device} seq_len={seq_len} window_agg={window_agg} threshold={threshold:.4f}")

    session = EbpfSession(container=args.container)
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
                    rows, timestamps = encode_tail(vocabs, raw_tail, use_arg_count_feature, arg_count_buckets)
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

    csv_path = out_dir / f"{args.service}_{run_id}_scores.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_unix", "nll", "alert"])
        for ts, score, alert in zip(history_ts, history_scores, history_alert):
            writer.writerow([f"{ts:.6f}", f"{score:.6f}", int(alert)])
    print(f"Історію вікон збережено: {csv_path}")

    window_end_ts = np.array(history_ts, dtype=np.float64)
    scores = np.array(history_scores, dtype=np.float64)
    attack_start_sec = (window_end_ts[0] + args.attack_marker) if args.attack_marker is not None else None
    plot_path = out_dir / f"{args.service}_{run_id}_nll_timeline.png"
    plot_file_timeline(
        f"{args.service} realtime ({run_id})", window_end_ts, scores, attack_start_sec, threshold, plot_path
    )
    print(f"Графік збережено: {plot_path}")

    n_alerts = sum(history_alert)
    print(f"Ітог: {len(history_scores)} вікон, {n_alerts} алертов ({100 * n_alerts / len(history_scores):.1f}%)")


if __name__ == "__main__":
    main()