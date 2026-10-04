"""Побудова кривих функції втрат та точності (Precision) за епохами з логу train.py.

Приклади:
    python plot_log_curves.py train.log
    python plot_log_curves.py train.log --output curves.png --dpi 300
    python plot_log_curves.py train.log --separate   # окремі файли для втрат і точності
"""
import argparse
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter, MaxNLocator

TRAIN_COLOR = "#2E86AB"
VAL_COLOR = "#E4572E"
BEST_COLOR = "#2A9D55"

_NUM = r"([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)"
_METRICS_RE = re.compile(
    r"епоха\s+(\d+)/\d+;[^\n]*\n"
    r"\s*Навчальна вибірка:[^\n]*?\(Loss\)\s*=\s*" + _NUM + r"\s+Точність \(Precision\)\s*=\s*" + _NUM + r"[^\n]*\n"
    r"\s*Валідаційна вибірка:[^\n]*?\(Loss\)\s*=\s*" + _NUM + r"\s+Точність \(Precision\)\s*=\s*" + _NUM
)


def parse_log(text: str) -> dict[str, list[float]]:
    """Витягує з логу метрики за епохами. Якщо епоха зустрічається кілька разів
    (наприклад, після донавчання), береться останній запис."""
    by_epoch: dict[int, tuple[float, float, float, float]] = {}
    for m in _METRICS_RE.finditer(text):
        epoch = int(m.group(1))
        by_epoch[epoch] = tuple(float(m.group(i)) for i in range(2, 6))

    epochs = sorted(by_epoch)
    return {
        "epoch": epochs,
        "train_loss": [by_epoch[e][0] for e in epochs],
        "train_precision": [by_epoch[e][1] for e in epochs],
        "val_loss": [by_epoch[e][2] for e in epochs],
        "val_precision": [by_epoch[e][3] for e in epochs],
    }


def _apply_style() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.facecolor": "#FAFAFA",
        "figure.facecolor": "white",
        "axes.edgecolor": "#B0B0B0",
        "axes.linewidth": 1.0,
        "axes.titleweight": "bold",
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
    })


def _draw_panel(
    ax: plt.Axes,
    epochs: list[int],
    train: list[float],
    val: list[float],
    title: str,
    ylabel: str,
    y_format: str,
    best_mode: str,
) -> None:
    marker_kw = dict(marker="o", markersize=5.5, markeredgecolor="white", markeredgewidth=1.0) if len(epochs) <= 40 else {}

    ax.plot(epochs, train, color=TRAIN_COLOR, linewidth=2.2, label="Навчальна вибірка", zorder=3, **marker_kw)
    ax.plot(epochs, val, color=VAL_COLOR, linewidth=2.2, label="Валідаційна вибірка", zorder=3, **marker_kw)

    best_idx = val.index(min(val) if best_mode == "min" else max(val))
    best_label = "мін." if best_mode == "min" else "макс."
    ax.scatter(
        [epochs[best_idx]], [val[best_idx]],
        s=170, marker="*", color=BEST_COLOR, edgecolor="white", linewidth=1.0, zorder=5,
        label=f"Найкраща епоха ({best_label} на валід.): {epochs[best_idx]}",
    )

    ax.set_title(title, pad=12)
    ax.set_xlabel("Епоха")
    ax.set_ylabel(ylabel)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.yaxis.set_major_formatter(FormatStrFormatter(y_format))
    ax.grid(True, color="#D9D9D9", linewidth=0.8, alpha=0.8, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.margins(x=0.03, y=0.12)
    ax.legend(frameon=True, facecolor="white", edgecolor="#D0D0D0", framealpha=0.95, loc="best")


def plot_curves(data: dict[str, list[float]], output: Path, dpi: int, separate: bool, title: str) -> list[Path]:
    _apply_style()
    epochs = data["epoch"]
    saved: list[Path] = []

    panels = {
        "loss": dict(
            train=data["train_loss"], val=data["val_loss"],
            title="Функція втрат", ylabel="Значення функції втрат (Loss)",
            y_format="%.4f", best_mode="min",
        ),
        "precision": dict(
            train=data["train_precision"], val=data["val_precision"],
            title="Точність", ylabel="Точність (Precision)",
            y_format="%.3f", best_mode="max",
        ),
    }

    if separate:
        for name, kw in panels.items():
            fig, ax = plt.subplots(figsize=(8, 5.5))
            _draw_panel(ax, epochs, **kw)
            fig.tight_layout()
            path = output.with_name(f"{output.stem}_{name}{output.suffix}")
            fig.savefig(path, dpi=dpi, bbox_inches="tight")
            plt.close(fig)
            saved.append(path)
    else:
        fig, axes = plt.subplots(1, 2, figsize=(15, 5.8))
        for ax, kw in zip(axes, panels.values()):
            _draw_panel(ax, epochs, **kw)
        if title:
            fig.suptitle(title, fontsize=16, fontweight="bold", y=1.02)
        fig.tight_layout()
        fig.savefig(output, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        saved.append(output)

    return saved


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("log", help="Шлях до текстового логу виводу train.py")
    parser.add_argument("--output", default="training_curves.png", help="Ім'я вихідного файлу (за замовчуванням training_curves.png)")
    parser.add_argument("--dpi", type=int, default=200, help="Роздільна здатність зображення (за замовчуванням 200)")
    parser.add_argument("--separate", action="store_true", help="Зберегти графіки втрат і точності в окремі файли")
    parser.add_argument("--title", default="Динаміка навчання моделі", help="Загальний заголовок (порожній рядок — без заголовка)")
    args = parser.parse_args()

    text = Path(args.log).read_text(encoding="utf-8", errors="ignore")
    data = parse_log(text)
    if not data["epoch"]:
        sys.exit("У логу не знайдено жодного блоку метрик (епоха + навчальна/валідаційна вибірка).")

    print(f"Знайдено епох з метриками: {len(data['epoch'])} ({data['epoch'][0]}–{data['epoch'][-1]})")
    for path in plot_curves(data, Path(args.output), args.dpi, args.separate, args.title):
        print(f"Збережено: {path}")


if __name__ == "__main__":
    main()