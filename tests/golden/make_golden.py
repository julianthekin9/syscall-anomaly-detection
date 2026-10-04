"""Генерація еталонних значень для tests/test_regression.py.

Запускається проти СТАРОГО коду (до переїзду в пакет, коміт 3c9ffac), тому
syscall_hids не імпортує. Старий код підключається через sys.path.

Usage:
    # один раз: фікстури — перші рядки кількох записів test-спліту
    python tests/golden/make_golden.py --make-fixtures DATASET_LIDDS/PHP_CWE-434/test

    # еталонні скори зі старого коду
    git worktree add ../old 3c9ffac
    python tests/golden/make_golden.py --old-code ../old
    git worktree remove ../old
"""

import argparse
import json
import sys
from pathlib import Path

GOLDEN_DIR = Path(__file__).resolve().parent
DATA_DIR = GOLDEN_DIR / "data"
CHECKPOINT = GOLDEN_DIR / "FLASK.pt"
GOLDEN_JSON = GOLDEN_DIR / "golden.json"
GROUPS = ("normal", "abnormal")
FILES_PER_GROUP = 3
LINES_PER_FILE = 1000


def make_fixtures(src: Path) -> None:
    """Перші LINES_PER_FILE рядків перших FILES_PER_GROUP записів кожної групи."""
    for group in GROUPS:
        out = DATA_DIR / group
        out.mkdir(parents=True, exist_ok=True)
        for path in sorted((src / group).glob("*.sc"))[:FILES_PER_GROUP]:
            with open(path, encoding="utf-8") as f:
                head = [line for _, line in zip(range(LINES_PER_FILE), f)]
            (out / path.name).write_text("".join(head), encoding="utf-8")
            print(f"{group}/{path.name}: {len(head)} рядків")


def make_golden(old_code: Path) -> None:
    sys.path.insert(0, str(old_code.resolve()))
    import torch
    from sklearn.metrics import roc_auc_score

    import config
    # У коміті 3c9ffac стоїть DATASET_FORMAT="lid_ds" (парсер 8-колонкового LID-DS).
    # Пакет syscall_hids відповідає гілці "generic" (data.py), тож еталон рахується в ній;
    # встановлюється до імпорту predict, бо той обирає парсер під час імпорту.
    config.DATASET_FORMAT = "generic"
    from model import SyscallLSTM
    from predict import score_log_file

    device = torch.device("cpu")
    checkpoint = torch.load(CHECKPOINT, map_location=device)
    model = SyscallLSTM.from_checkpoint(checkpoint, device)
    model.eval()

    scores: dict[str, list[float]] = {}
    truth: list[bool] = []
    flat: list[float] = []
    for group in GROUPS:
        for path in sorted((DATA_DIR / group).glob("*.sc")):
            s = score_log_file(model, checkpoint, str(path), device)
            scores[f"{group}/{path.name}"] = s
            truth += [group == "abnormal"] * len(s)
            flat += s

    golden = {"old_code_commit": "3c9ffac", "auc": roc_auc_score(truth, flat), "scores": scores}
    GOLDEN_JSON.write_text(json.dumps(golden, indent=1), encoding="utf-8")
    print(f"{len(flat)} вікон, AUC={golden['auc']:.6f} -> {GOLDEN_JSON}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--make-fixtures", type=Path, metavar="TEST_SPLIT_DIR")
    group.add_argument("--old-code", type=Path, metavar="OLD_CODE_DIR")
    args = parser.parse_args()
    if args.make_fixtures:
        make_fixtures(args.make_fixtures)
    else:
        make_golden(args.old_code)


if __name__ == "__main__":
    main()
