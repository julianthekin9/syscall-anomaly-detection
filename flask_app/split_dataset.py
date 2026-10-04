"""
Розбиває один великий файл трасу на train/val за часом: перші train_ratio рядків
ідуть у train, решта у val. Рядки не перемішуються: для трас syscall'ів порядок
є самими даними, перемішування його руйнує.

Працює потоково у два проходи, файл цілком у пам'ять не читається:
перший прохід рахує рядки, другий пише їх у train/val. Байти рядків
копіюються без змін. Заголовок (header), якщо є, копіюється в обидва файли.

Приклади використання:
    # 90% train / 10% val
    python flask_app/split_dataset.py --input normal.sc --train-ratio 0.9

    # власні шляхи для виводу
    python flask_app/split_dataset.py --input normal.sc --train-ratio 0.8 \
        --train-out training/train.sc --val-out validation/validation.sc
"""

import argparse
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

    # Прохід 1: кількість рядків даних (без заголовка)
    with input_path.open("rb") as f:
        n_lines = sum(1 for _ in f) - (1 if args.header else 0)

    if args.header and n_lines < 0:
        sys.exit("Вхідний файл порожній, але вказано --header")
    if n_lines <= 0:
        sys.exit("У вхідному файлі немає рядків даних для розбиття")

    split_idx = round(n_lines * args.train_ratio)
    # гарантуємо, що обидві вибірки непорожні, якщо у файлі є хоча б 2 рядки
    split_idx = max(1, min(split_idx, n_lines - 1)) if n_lines > 1 else split_idx

    # Прохід 2: перші split_idx рядків у train, решта у val
    for path in (train_path, val_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open("rb") as src, train_path.open("wb") as train_f, val_path.open("wb") as val_f:
        if args.header:
            header_line = src.readline()
            train_f.write(header_line)
            val_f.write(header_line)
        for i, line in enumerate(src):
            (train_f if i < split_idx else val_f).write(line)

    n_val = n_lines - split_idx
    print(f"Всього рядків даних: {n_lines}")
    print(f"Train: {split_idx} рядків ({split_idx / n_lines:.1%}) -> {train_path}")
    print(f"Val:   {n_val} рядків ({n_val / n_lines:.1%}) -> {val_path}")


if __name__ == "__main__":
    main()
