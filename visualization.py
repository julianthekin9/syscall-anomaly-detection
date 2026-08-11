"""Построение графика метрик train/val по эпохам (loss + macro-precision,
отдельно syscall и process). Вызывается из train.py в конце обучения
каждого сервиса — см. train.plot_training_curves нет, функция здесь:
visualization.plot_training_curves(service_name, history).

history — словарь списков одинаковой длины (по одному элементу на каждую
"метрическую" эпоху, см. config.METRICS_EVAL_EVERY_N_EPOCHS):
    "epoch": [1, 3, 5, ...]
    "train_loss_syscall": [...], "val_loss_syscall": [...]
    "train_precision_syscall": [...], "val_precision_syscall": [...]
    "train_loss_process": [...], "val_loss_process": [...]              (опционально)
    "train_precision_process": [...], "val_precision_process": [...]    (опционально)

matplotlib используется с backend'ом Agg (без дисплея) — обучение обычно
идёт на сервере без GUI.
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config


def plot_training_curves(service_name: str, history: dict[str, list[float]]) -> str | None:
    """Сохраняет PNG с графиками loss/precision по эпохам в
    config.PLOTS_DIR/<service_name>_epochs.png. Возвращает путь к файлу,
    либо None, если history пуста (метрики ни разу не считались — например
    если config.METRICS_EVAL_EVERY_N_EPOCHS больше числа эпох и последняя
    эпоха почему-то не попала в замер)."""
    epochs = history.get("epoch", [])
    if not epochs:
        print(f"[{service_name}] history пуста — график не строю")
        return None

    has_process = "train_loss_process" in history and "val_loss_process" in history

    ncols = 2 if has_process else 1
    fig, axes = plt.subplots(2, ncols, figsize=(6 * ncols, 8), squeeze=False)

    def _plot(ax, train_key: str, val_key: str, title: str, ylim01: bool = False) -> None:
        ax.plot(epochs, history[train_key], marker="o", label="train")
        ax.plot(epochs, history[val_key], marker="o", label="val")
        ax.set_title(title)
        ax.set_xlabel("эпоха")
        if ylim01:
            ax.set_ylim(0, 1.02)
        ax.grid(alpha=0.3)
        ax.legend()

    _plot(axes[0][0], "train_loss_syscall", "val_loss_syscall", "Loss (syscall)")
    _plot(axes[1][0], "train_precision_syscall", "val_precision_syscall", "Macro precision (syscall)", ylim01=True)

    if has_process:
        _plot(axes[0][1], "train_loss_process", "val_loss_process", "Loss (process)")
        _plot(axes[1][1], "train_precision_process", "val_precision_process", "Macro precision (process)", ylim01=True)

    fig.suptitle(f"{service_name}: метрики по эпохам")
    fig.tight_layout()

    os.makedirs(config.PLOTS_DIR, exist_ok=True)
    out_path = os.path.join(config.PLOTS_DIR, f"{service_name}_epochs.png")
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path