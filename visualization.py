import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config


def plot_training_curves(service_name: str, history: dict[str, list[float]]) -> str | None:
    epochs = history.get("epoch", [])
    if not epochs:
        print(f"[{service_name}] history порожня — графік не будую")
        return None

    fig, axes = plt.subplots(2, 1, figsize=(6, 8), squeeze=False)

    def _plot(ax, train_key: str, val_key: str, title: str, ylim01: bool = False) -> None:
        ax.plot(epochs, history[train_key], marker="o", label="train")
        ax.plot(epochs, history[val_key], marker="o", label="val")
        ax.set_title(title)
        ax.set_xlabel("епоха")
        if ylim01:
            ax.set_ylim(0, 1.02)
        ax.grid(alpha=0.3)
        ax.legend()

    _plot(axes[0][0], "train_loss_syscall", "val_loss_syscall", "Loss (syscall)")
    _plot(axes[1][0], "train_precision_syscall", "val_precision_syscall", "Macro precision (syscall)", ylim01=True)

    fig.suptitle(f"{service_name}: метрики по епохах")
    fig.tight_layout()

    os.makedirs(config.PLOTS_DIR, exist_ok=True)
    out_path = os.path.join(config.PLOTS_DIR, f"{service_name}_epochs.png")
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path