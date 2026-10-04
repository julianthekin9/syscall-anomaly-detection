import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import config


def plot_training_curves(service_name: str, history: dict[str, list[float]]) -> str | None:
    epochs = history.get("epoch", [])
    if not epochs:
        print(f"[{service_name}] history порожня — графік не будую")
        return None

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

    os.makedirs(config.PLOTS_DIR, exist_ok=True)
    out_path = os.path.join(config.PLOTS_DIR, f"{service_name}_epochs.png")
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path

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

def plot_roc_curve(truth: list[bool], scores: list[float], service_name: str, auc: float) -> None:
    """Побудова та збереження ROC-кривої."""
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

    path = f"roc_curve_{service_name}.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"[{service_name}] ROC-криву збережено у {path}")