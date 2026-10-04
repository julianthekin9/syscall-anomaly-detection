"""Генерація еталонних значень для регресійних тестів (tests/README.md).

Запускається проти СТАРОГО коду (до переїзду в пакет, коміт 3c9ffac), тому
syscall_hids не імпортує. Старий код підключається через sys.path.

Usage:
    # один раз: фікстури інференсу — перші рядки кількох записів test-спліту
    python tests/golden/make_golden.py --make-fixtures DATASET_LIDDS/PHP_CWE-434/test
    # один раз: міні-датасет FIXT для еталону навчання
    python tests/golden/make_golden.py --make-fixt DATASET_LIDDS/PHP_CWE-434

    git worktree add ../old 3c9ffac
    # еталонні скори інференсу на FLASK.pt
    python tests/golden/make_golden.py --old-code ../old
    # еталон міні-навчання на FIXT (+ FIXT.pt та скори інференсу на ньому)
    python tests/golden/make_golden.py --old-code ../old --train
    git worktree remove ../old

Кожен режим оновлює лише свої ключі в golden.json.
"""

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

GOLDEN_DIR = Path(__file__).resolve().parent
DATA_DIR = GOLDEN_DIR / "data"
CHECKPOINT = GOLDEN_DIR / "FLASK.pt"
FIXT_CHECKPOINT = GOLDEN_DIR / "FIXT.pt"
GOLDEN_JSON = GOLDEN_DIR / "golden.json"
GROUPS = ("normal", "abnormal")
FILES_PER_GROUP = 3
LINES_PER_FILE = 1000
OLD_CODE_COMMIT = "3c9ffac"

FIXT = "FIXT"
FIXT_DIR = DATA_DIR / FIXT
# Скільки записів (по LINES_PER_FILE рядків) береться в train/val міні-датасету
FIXT_SPLIT_FILES = {"training": 3, "validation": 2}
# Усі параметри config, від яких залежить навчання, задаються явно: еталон не
# залежить від умовчань ні старого, ні нового коду. Тест бере їх із golden.json.
FIXT_CONFIG = {
    "SERVICES": [FIXT],
    "USE_ARG_COUNT_FEATURE": True,
    "ARG_COUNT_BUCKETS": 8,
    "FORCE_REBUILD_VOCAB": True,
    "EMBED_DIM_SYSCALL": 16,
    "EMBED_DIM_PROCESS": 8,
    "EMBED_DIM_DIRECTION": 2,
    "EMBED_DIM_ARG_COUNT": 4,
    "HIDDEN_DIM": 32,
    "NUM_LAYERS": 2,
    "DROPOUT": 0.2,
    "SEQ_LEN": 64,
    "SEQ_STEP": 32,
    "BATCH_SIZE": 16,
    "LEARNING_RATE": 1e-3,
    "EPOCHS": 2,
    "RESUME": False,
    "WINDOW_AGG": "quantile",
    "WINDOW_AGG_QUANTILE": 0.9,
    "THRESHOLD_PERCENTILE": 99.0,
    "EVAL_TEST_EVERY_EPOCH": True,
    "METRICS_EVAL_EVERY_N_EPOCHS": 1,
    "TRAIN_METRICS_MAX_BATCHES": None,
    "RAM_GUARD_ENABLED": False,
}
SEED = 0


def _head(path: Path) -> str:
    with open(path, encoding="utf-8") as f:
        return "".join(line for _, line in zip(range(LINES_PER_FILE), f))


def _update_golden(**keys) -> None:
    golden = json.loads(GOLDEN_JSON.read_text(encoding="utf-8")) if GOLDEN_JSON.exists() else {}
    golden.update(keys)
    GOLDEN_JSON.write_text(json.dumps(golden, indent=1), encoding="utf-8")


def make_fixtures(src: Path) -> None:
    """Перші LINES_PER_FILE рядків перших FILES_PER_GROUP записів кожної групи."""
    for group in GROUPS:
        out = DATA_DIR / group
        out.mkdir(parents=True, exist_ok=True)
        for path in sorted((src / group).glob("*.sc"))[:FILES_PER_GROUP]:
            (out / path.name).write_text(_head(path), encoding="utf-8")
            print(f"{group}/{path.name}")


def make_fixt(scenario_dir: Path) -> None:
    """Міні-датасет FIXT: train/val з нормальних записів сценарію, test — копія фікстур інференсу."""
    for split, n in FIXT_SPLIT_FILES.items():
        out = FIXT_DIR / split
        out.mkdir(parents=True, exist_ok=True)
        for path in sorted((scenario_dir / split).glob("*.sc"))[:n]:
            (out / path.name).write_text(_head(path), encoding="utf-8")
            print(f"{FIXT}/{split}/{path.name}")
    for group in GROUPS:
        shutil.copytree(DATA_DIR / group, FIXT_DIR / "test" / group, dirs_exist_ok=True)
        print(f"{FIXT}/test/{group} <- data/{group}")


def _import_old_code(old_code: Path):
    sys.path.insert(0, str(old_code.resolve()))
    import config
    # У коміті 3c9ffac стоїть DATASET_FORMAT="lid_ds" (парсер 8-колонкового LID-DS).
    # Пакет syscall_hids відповідає гілці "generic" (data.py), тож еталон рахується в ній;
    # встановлюється до імпорту predict/train, бо вони обирають парсер під час імпорту.
    config.DATASET_FORMAT = "generic"
    return config


def _score_files(score_log_file, model, checkpoint, files: dict[str, Path], device) -> dict:
    from sklearn.metrics import roc_auc_score

    scores: dict[str, list[float]] = {}
    truth: list[bool] = []
    flat: list[float] = []
    for name, path in files.items():
        s = score_log_file(model, checkpoint, str(path), device)
        scores[name] = s
        truth += [name.startswith("abnormal/")] * len(s)
        flat += s
    return {"auc": roc_auc_score(truth, flat), "scores": scores}


def _group_files(root: Path) -> dict[str, Path]:
    return {f"{g}/{p.name}": p for g in GROUPS for p in sorted((root / g).glob("*.sc"))}


def make_golden(old_code: Path) -> None:
    _import_old_code(old_code)
    import torch
    from model import SyscallLSTM
    from predict import score_log_file

    device = torch.device("cpu")
    checkpoint = torch.load(CHECKPOINT, map_location=device)
    model = SyscallLSTM.from_checkpoint(checkpoint, device)
    model.eval()

    res = _score_files(score_log_file, model, checkpoint, _group_files(DATA_DIR), device)
    _update_golden(old_code_commit=OLD_CODE_COMMIT, **res)
    print(f"FLASK: {sum(map(len, res['scores'].values()))} вікон, AUC={res['auc']:.6f} -> {GOLDEN_JSON}")


def make_train_golden(old_code: Path) -> None:
    config = _import_old_code(old_code)
    import random

    import numpy as np
    import torch
    import train
    from model import SyscallLSTM
    from predict import score_log_file

    device = torch.device("cpu")
    history: dict = {}
    test_aucs: list[float] = []
    # Метрики знімаються на вході функцій малювання; картинки не пишуться
    train.plot_training_curves = lambda service, h: history.update(h)
    train.plot_roc_curve = lambda *a: test_aucs.append(a[3])

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for key, value in FIXT_CONFIG.items():
            setattr(config, key, value)
        config.DATASET_ROOT = str(DATA_DIR)
        config.MODEL_DIR = str(tmp_path / "models")
        config.CHECKPOINT_DIR = str(tmp_path / "models" / "checkpoints")
        config.VOCAB_DIR = str(tmp_path / "vocabs")
        config.PLOTS_DIR = str(tmp_path / "plots")
        cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            random.seed(SEED)
            np.random.seed(SEED)
            torch.manual_seed(SEED)
            torch.use_deterministic_algorithms(True)
            train.train_one_service(FIXT, device)
        finally:
            os.chdir(cwd)
        shutil.copy(tmp_path / "models" / f"{FIXT}.pt", FIXT_CHECKPOINT)

    checkpoint = torch.load(FIXT_CHECKPOINT, map_location=device)
    golden_train = {
        "config": FIXT_CONFIG,
        "seed": SEED,
        "vocabs": checkpoint["vocabs"],
        "vocab_sizes": checkpoint["vocab_sizes"],
        "hparams": checkpoint["hparams"],
        "threshold": checkpoint["threshold"],
        "epochs_trained": checkpoint["epochs_trained"],
        "history": history,
        "test_auc_per_epoch": test_aucs,
        "state_dict": {k: [v.double().sum().item(), v.double().norm().item()] for k, v in checkpoint["model_state"].items()},
    }

    model = SyscallLSTM.from_checkpoint(checkpoint, device)
    model.eval()
    fixt_inference = _score_files(score_log_file, model, checkpoint, _group_files(FIXT_DIR / "test"), device)

    _update_golden(old_code_commit=OLD_CODE_COMMIT, train=golden_train, fixt_inference=fixt_inference)
    print(f"FIXT: поріг={golden_train['threshold']:.6f}, AUC по епохах={test_aucs}, "
          f"інференс FIXT.pt AUC={fixt_inference['auc']:.6f} -> {GOLDEN_JSON}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--make-fixtures", type=Path, metavar="TEST_SPLIT_DIR")
    group.add_argument("--make-fixt", type=Path, metavar="SCENARIO_DIR")
    group.add_argument("--old-code", type=Path, metavar="OLD_CODE_DIR")
    parser.add_argument("--train", action="store_true", help="З --old-code: еталон міні-навчання на FIXT")
    args = parser.parse_args()
    if args.make_fixtures:
        make_fixtures(args.make_fixtures)
    elif args.make_fixt:
        make_fixt(args.make_fixt)
    elif args.train:
        make_train_golden(args.old_code)
    else:
        make_golden(args.old_code)


if __name__ == "__main__":
    main()
