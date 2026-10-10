"""
Usage:
    hids-eval --service FLASK --log path/to/log.sc
    hids-eval --service FLASK --eval-test-split
    hids-eval --config configs/php_cwe_434.yaml --service PHP_CWE-434 --eval-test-split
"""

import logging
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from syscall_hids.data.datasets import SequenceDataset, TestSequenceDataset
from syscall_hids.data.parsing import read_recording
from syscall_hids.data.sequences import build_test_sequences, encode_recording, make_sequences
from syscall_hids.modules.models import SyscallLSTM
from syscall_hids.modules.scoring import aggregate_window_scores, compute_step_scores
from syscall_hids.tools import resource_guard
from syscall_hids.tools.arg_parser import build_eval_arg_parser
from syscall_hids.tools.arg_parser_tools import check_args
from syscall_hids.tools.checkpoint import checkpoint_features, load_model
from syscall_hids.tools.evaluation import quick_test_evaluation

def score_log_file(
    model: SyscallLSTM, checkpoint: dict, log_path: str, device: torch.device, batch_size: int
) -> list[float]:
    vocabs = checkpoint["vocabs"]
    seq_len = checkpoint["seq_len"]

    lines = read_recording(log_path)
    if not lines:
        raise ValueError(f"Can't parse any line from {log_path}")

    encoded = encode_recording(vocabs, lines, *checkpoint_features(checkpoint))
    X, y = make_sequences(encoded, seq_len, seq_len)
    if len(X) == 0:
        raise ValueError(f"Log shorter than {seq_len + 1} events — not enough events for new window.")

    loader = DataLoader(SequenceDataset(X, y), batch_size=batch_size, shuffle=False)

    scores: list[float] = []
    with torch.no_grad():
        for x, y_batch in loader:
            x, y_batch = x.to(device), y_batch.to(device)
            logits_syscall = model(x)
            step_scores = compute_step_scores(logits_syscall, y_batch)
            window_scores = aggregate_window_scores(
                step_scores,
                window_agg=checkpoint["window_agg"],
                window_agg_quantile=checkpoint["window_agg_quantile"],
            )
            scores.extend(window_scores.cpu().tolist())
    return scores


def print_log_verdict(scores: list[float], threshold: float) -> None:
    print(f"{len(scores)} window(s), alert threshold = {threshold:.4f}")
    alerts = 0
    for i, score in enumerate(scores, start=1):
        marker = "  <-- ALERT" if score > threshold else ""
        print(f"  window {i}: anomaly_score={score:.4f}{marker}")
        if score > threshold:
            alerts += 1

    if alerts:
        print(f"\nSUMMARY: {alerts}/{len(scores)} windows exceeded the alert threshold, suspicious activity")
    else:
        print(f"\nSUMMARY: all {len(scores)} windows are within normal range.")


def main() -> None:
    # quick_test_evaluation and plot_roc_curve write via logging: print to the console as before
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = build_eval_arg_parser(description=__doc__)
    parser.add_argument("--checkpoint", default=None, help="Explicit path to the .pt (default: {model_dir}/<service>.pt)")
    args = parser.parse_args()

    if not args.log and not args.eval_test_split:
        parser.error("Specify --log <file> or --eval-test-split")

    args, input_log_messages = check_args(args)
    for message, _ in input_log_messages:
        print(f"WARNING: {message}")
    resource_guard.configure(
        args.ram_guard_enabled, args.ram_soft_limit_percent, args.ram_hard_limit_percent, args.ram_throttle_sleep_sec
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if args.checkpoint:
        checkpoint_path = Path(args.checkpoint)
        model, checkpoint = load_model(checkpoint_path.stem, device, str(checkpoint_path.parent))
    else:
        model, checkpoint = load_model(args.service, device, args.model_dir)
    threshold = checkpoint["threshold"]

    if args.log:
        scores = score_log_file(model, checkpoint, args.log, device, args.batch_size)
        print(f"File {args.log}:")
        print_log_verdict(scores, threshold)

    if args.eval_test_split:
        vocabs = checkpoint["vocabs"]
        seq_len = checkpoint["seq_len"]
        features, arg_count_buckets = checkpoint_features(checkpoint)
        X_test, y_test, window_is_attack = build_test_sequences(
            args.service, vocabs, seq_len, seq_len,
            args.dataset_root, features, arg_count_buckets, args.ram_check_every_n_recordings,
        )
        if len(X_test) == 0:
            print(f"[{args.service}] test split is empty or shorter than SEQ_LEN+1")
            return
        test_loader = DataLoader(TestSequenceDataset(X_test, y_test, window_is_attack), batch_size=args.batch_size, shuffle=False)
        print(f"\nEvaluation on the test split of service {args.service} ({len(X_test)} windows):")
        # window aggregation is the one the model was calibrated with (from the checkpoint), not from the arguments
        quick_test_evaluation(
            model, test_loader, threshold, device, args.service, ("eval",),
            checkpoint["window_agg"], checkpoint["window_agg_quantile"], args.plots_dir,
        )


if __name__ == "__main__":
    main()
