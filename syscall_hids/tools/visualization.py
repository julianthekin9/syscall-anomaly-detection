import json
import logging
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def plot_training_curves(service_name: str, history: dict[str, list[float]], plots_dir: str) -> str | None:
    if not history.get("epoch", []):
        logging.warning(f"[{service_name}] history порожня — графік не будую")
        return None

    os.makedirs(plots_dir, exist_ok=True)
    out_path = os.path.join(plots_dir, f"{service_name}_epochs.png")
    _draw_training_curves(history, out_path)
    return out_path


def plot_from_results(results_path: str, out_path: str) -> str | None:
    """Ті самі криві, що й plot_training_curves, але з файлу метрик JSONL (записи mode="eval")."""
    by_epoch: dict[int, dict[str, float]] = {}
    with open(results_path, encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            if record.get("mode") == "eval":
                metrics = by_epoch.setdefault(record["epoch"], {})
                metrics[f"{record['split']}_loss_syscall"] = record["loss"]
                metrics[f"{record['split']}_precision_syscall"] = record["precision"]
    epochs = sorted(by_epoch)
    if not epochs:
        logging.warning(f"{results_path}: немає записів eval — графік не будую")
        return None

    history: dict[str, list[float]] = {"epoch": epochs}
    for key in ("train_loss_syscall", "val_loss_syscall", "train_precision_syscall", "val_precision_syscall"):
        history[key] = [by_epoch[e][key] for e in epochs]
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    _draw_training_curves(history, out_path)
    return out_path


def _draw_training_curves(history: dict[str, list[float]], out_path: str) -> None:
    epochs = history["epoch"]
    fig, axes = plt.subplots(2, 1, figsize=(6, 8), squeeze=False)

    def _plot(ax, train_key: str, val_key: str, title: str, ylim01: bool = False) -> None:
        ax.plot(epochs, history[train_key], marker="o", label="Навчальна вибірка")
        ax.plot(epochs, history[val_key], marker="o", label="Валідаційна вибірка")
        ax.set_title(title)
        ax.set_xlabel("епоха")
        if ylim01:
            ax.set_ylim(0, 1.02)
        ax.grid(alpha=0.3)
        ax.legend()

    _plot(axes[0][0], "train_loss_syscall", "val_loss_syscall", "Функція втрат (Loss)")
    _plot(axes[1][0], "train_precision_syscall", "val_precision_syscall", "Точність (Precision)", ylim01=True)

    fig.suptitle("Метрики по епохах")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)

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
        color="#2563eb", label="Час нормальної поведінки", s=18, zorder=2,
    )
    if is_attack_window.any():
        ax.scatter(
            rel_t[is_attack_window], scores[is_attack_window],
            color="#dc2626", label="Час аномальної поведінки", s=18, zorder=2,
        )

    ax.axhline(threshold, color="#16a34a", linestyle="--", linewidth=1.2, label=f"threshold = {threshold:.4f}")
    if attack_start_sec is not None:
        ax.axvline(attack_start_sec - t0, color="#dc2626", linestyle=":", linewidth=1.5, label="Початок аномальної поведінки (info.json)")

    ax.set_xlabel("Час від початку запису, с")
    ax.set_ylabel("NLL (anomaly score)")
    ax.set_title(f"{filename} — NLL по часовим меткам лога")
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)

def plot_roc_curve(
    truth: list[bool], scores: list[float], service_name: str, auc: float, tags: tuple[str, ...], plots_dir: str
) -> None:
    """Побудова ROC-кривої; зберігається в plots_dir як <сервіс>_roc_<тег>.png для кожного тегу."""
    from sklearn.metrics import roc_curve

    fpr, tpr, _ = roc_curve(truth, scores)

    plt.figure(figsize=(7, 6))
    plt.plot(fpr, tpr, label=f"ROC-AUC = {auc:.4f}")
    plt.plot([0, 1], [0, 1], linestyle="--", label="Random classifier")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title(f"ROC-крива — {service_name}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    os.makedirs(plots_dir, exist_ok=True)
    for tag in tags:
        path = os.path.join(plots_dir, f"{service_name}_roc_{tag}.png")
        plt.savefig(path, dpi=150)
        logging.debug(f"[{service_name}] ROC-криву збережено у {path}")
    plt.close()