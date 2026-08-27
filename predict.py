"""
Usage:
    python predict.py --service FLASK --log путь/к/логу.sc
    python predict.py --service FLASK --eval-test-split
"""

import argparse
import os

import torch
from torch.utils.data import DataLoader

import config
from data import build_test_sequences, encode_recording, make_sequences, read_recording
from dataset import TestSequenceDataset, SequenceDataset
from model import SyscallLSTM, aggregate_window_scores, compute_step_scores
from train import quick_test_evaluation


def load_model(service_name: str, device: torch.device) -> tuple[SyscallLSTM, dict]:
    path = os.path.join(config.MODEL_DIR, f"{service_name}.pt")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Checkpoint {path} not found — train the model first: python train.py --service {service_name}")

    checkpoint = torch.load(path, map_location=device)
    model = SyscallLSTM.from_checkpoint(checkpoint, device)
    model.eval()
    return model, checkpoint


def score_log_file(model: SyscallLSTM, checkpoint: dict, log_path: str, device: torch.device) -> list[float]:
    vocabs = checkpoint["vocabs"]
    seq_len = checkpoint["seq_len"]

    lines = read_recording(log_path)
    if not lines:
        raise ValueError(f"Can't parse any line from {log_path}")

    encoded = encode_recording(vocabs, lines)
    X, y = make_sequences(encoded, seq_len, seq_len)
    if len(X) == 0:
        raise ValueError(f"Log shorter than {seq_len + 1} events — not enough events for new window.")

    loader = DataLoader(SequenceDataset(X, y), batch_size=config.BATCH_SIZE, shuffle=False)

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
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--service", required=True, help="Имя сервиса (та же папка сценария, что при обучении)")
    parser.add_argument("--log", help="Путь к конкретному .sc-файлу для оценки")
    parser.add_argument("--eval-test-split", action="store_true", help="Оценить весь test-сплит сервиса (норма+атаки) с метриками качества")
    args = parser.parse_args()

    if not args.log and not args.eval_test_split:
        parser.error("Укажите --log <файл> или --eval-test-split")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, checkpoint = load_model(args.service, device)
    threshold = checkpoint["threshold"]

    if args.log:
        scores = score_log_file(model, checkpoint, args.log, device)
        print(f"Файл {args.log}:")
        print_log_verdict(scores, threshold)

    if args.eval_test_split:
        vocabs = checkpoint["vocabs"]
        seq_len = checkpoint["seq_len"]
        X_test, y_test, window_is_attack = build_test_sequences(args.service, vocabs, seq_len, seq_len)
        if len(X_test) == 0:
            print(f"[{args.service}] test-сплит пуст или короче SEQ_LEN+1")
            return
        test_loader = DataLoader(TestSequenceDataset(X_test, y_test, window_is_attack), batch_size=config.BATCH_SIZE, shuffle=False)
        print(f"\nОценка на test-сплите сервиса {args.service} ({len(X_test)} окон):")
        quick_test_evaluation(model, test_loader, threshold, device)


if __name__ == "__main__":
    main()