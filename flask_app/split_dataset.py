"""
Розбиває один великий файл датасету на train/val за заданим співвідношенням.

Працює побудрядково — кожен рядок вхідного файлу вважається окремим записом
(підходить для CSV, JSONL або текстових логів syscall-трейсів з одним записом
на рядок). Заголовок (header), якщо є, автоматично копіюється в обидва файли.

Приклади використання:
    # 90% train / 10% val, випадковий (shuffled) розподіл
    python split_dataset.py --input dataset.csv --train-ratio 0.9

    # без перемішування (зберегти хронологічний порядок) — перші N% у train,
    # решта у val; корисно для syscall-трейсів, де порядок важливий
    python split_dataset.py --input dataset.csv --train-ratio 0.9 --no-shuffle

    # з заголовком CSV (перший рядок скопіюється в train і val)
    python split_dataset.py --input dataset.csv --train-ratio 0.8 --header

    # власні шляхи для виводу та seed для відтворюваності
    python split_dataset.py --input dataset.csv --train-ratio 0.85 \
        --train-out train.csv --val-out val.csv --seed 42
"""

import argparse
import random
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--input", required=True, help="Шлях до вхідного файлу датасету")
    parser.add_argument(
        "--train-ratio", type=float, required=True,
        help="Частка даних для train, від 0 до 1 (наприклад 0.9 = 90%% train / 10%% val)",
    )
    parser.add_argument("--train-out", default=None, help="Шлях для train-файлу (за замовчуванням: <input>.train)")
    parser.add_argument("--val-out", default=None, help="Шлях для val-файлу (за замовчуванням: <input>.val)")
    parser.add_argument(
        "--header", action="store_true",
        help="Перший рядок вхідного файлу — заголовок; буде скопійований в обидва вихідні файли",
    )
    parser.add_argument(
        "--no-shuffle", action="store_true",
        help="Не перемішувати рядки — зберегти порядок (перші N%% у train, решта у val)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Seed для генератора випадкових чисел (за замовчуванням 42)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not 0.0 < args.train_ratio < 1.0:
        sys.exit(f"--train-ratio має бути в діапазоні (0, 1), отримано: {args.train_ratio}")

    input_path = Path(args.input)
    if not input_path.exists():
        sys.exit(f"Вхідний файл не знайдено: {input_path}")

    train_path = Path(args.train_out) if args.train_out else input_path.with_suffix(input_path.suffix + ".train")
    val_path = Path(args.val_out) if args.val_out else input_path.with_suffix(input_path.suffix + ".val")

    with input_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    header_line = None
    if args.header:
        if not lines:
            sys.exit("Вхідний файл порожній, але вказано --header")
        header_line = lines[0]
        lines = lines[1:]

    if not lines:
        sys.exit("У вхідному файлі немає рядків даних для розбиття")

    if not args.no_shuffle:
        rng = random.Random(args.seed)
        rng.shuffle(lines)

    split_idx = round(len(lines) * args.train_ratio)
    # гарантуємо, що обидві вибірки непорожні, якщо у файлі є хоча б 2 рядки
    split_idx = max(1, min(split_idx, len(lines) - 1)) if len(lines) > 1 else split_idx

    train_lines = lines[:split_idx]
    val_lines = lines[split_idx:]

    with train_path.open("w", encoding="utf-8") as f:
        if header_line is not None:
            f.write(header_line)
        f.writelines(train_lines)

    with val_path.open("w", encoding="utf-8") as f:
        if header_line is not None:
            f.write(header_line)
        f.writelines(val_lines)

    total = len(train_lines) + len(val_lines)
    print(f"Всього рядків даних: {total}")
    print(f"Train: {len(train_lines)} рядків ({len(train_lines) / total:.1%}) -> {train_path}")
    print(f"Val:   {len(val_lines)} рядків ({len(val_lines) / total:.1%}) -> {val_path}")
    print(f"Перемішування: {'вимкнено' if args.no_shuffle else f'увімкнено (seed={args.seed})'}")


if __name__ == "__main__":
    main()