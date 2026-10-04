"""
Usage:
    hids-eval --service FLASK --log путь/к/логу.sc
    hids-eval --service FLASK --eval-test-split
    hids-eval --config configs/php_cwe_434.yaml --service PHP_CWE-434 --eval-test-split
"""

import logging

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
    print(f"{len(scores)} окно(а), порог тревоги = {threshold:.4f}")
    alerts = 0
    for i, score in enumerate(scores, start=1):
        marker = "  <-- АЛЕРТ" if score > threshold else ""
        print(f"  окно {i}: anomaly_score={score:.4f}{marker}")
        if score > threshold:
            alerts += 1

    if alerts:
        print(f"\nІТОГ: {alerts}/{len(scores)} окон превысили порог тревоги — підозріла активність")
    else:
        print(f"\nІТОГ: усі {len(scores)} вікон в межах норми.")


def main() -> None:
    # quick_test_evaluation і plot_roc_curve пишуть через logging: виводимо в консоль як раніше
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = build_eval_arg_parser(description=__doc__)
    args = parser.parse_args()

    if not args.log and not args.eval_test_split:
        parser.error("Укажите --log <файл> или --eval-test-split")

    args, input_log_messages = check_args(args)
    for message, _ in input_log_messages:
        print(f"УВАГА: {message}")
    resource_guard.configure(
        args.ram_guard_enabled, args.ram_soft_limit_percent, args.ram_hard_limit_percent, args.ram_throttle_sleep_sec
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, checkpoint = load_model(args.service, device, args.model_dir)
    threshold = checkpoint["threshold"]

    if args.log:
        scores = score_log_file(model, checkpoint, args.log, device, args.batch_size)
        print(f"Файл {args.log}:")
        print_log_verdict(scores, threshold)

    if args.eval_test_split:
        vocabs = checkpoint["vocabs"]
        seq_len = checkpoint["seq_len"]
        use_arg_count_feature, arg_count_buckets = checkpoint_features(checkpoint)
        X_test, y_test, window_is_attack = build_test_sequences(
            args.service, vocabs, seq_len, seq_len,
            args.dataset_root, use_arg_count_feature, arg_count_buckets, args.ram_check_every_n_recordings,
        )
        if len(X_test) == 0:
            print(f"[{args.service}] test-сплит пуст или короче SEQ_LEN+1")
            return
        test_loader = DataLoader(TestSequenceDataset(X_test, y_test, window_is_attack), batch_size=args.batch_size, shuffle=False)
        print(f"\nОценка на test-сплите сервиса {args.service} ({len(X_test)} окон):")
        # агрегація вікна — та, з якою модель калібрувалась (з чекпоінта), а не з аргументів
        quick_test_evaluation(
            model, test_loader, threshold, device, args.service, ("eval",),
            checkpoint["window_agg"], checkpoint["window_agg_quantile"], args.plots_dir,
        )


if __name__ == "__main__":
    main()
