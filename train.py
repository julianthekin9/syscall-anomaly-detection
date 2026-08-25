import argparse
import gc
import os

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import classification_report, roc_auc_score
from torch.utils.data import DataLoader

import config
import resource_guard
from data import build_normal_sequences, build_test_sequences, build_vocab, list_services
from dataset import EvalSequenceDataset, SequenceDataset
from model import ARCHITECTURE_VERSION, ModelHParams, SyscallLSTM, aggregate_window_scores, compute_step_scores
from visualization import plot_training_curves


def _update_confusion(cm: torch.Tensor, y_true: torch.Tensor, y_pred: torch.Tensor, num_classes: int) -> None:
    """cm: [num_classes, num_classes] (рядки — істина, стовпці — передбачення),
    акумулюється за батчами через bincount """
    idx = y_true.reshape(-1).long() * num_classes + y_pred.reshape(-1).long()
    cm += torch.bincount(idx, minlength=num_classes * num_classes).reshape(num_classes, num_classes)


def _macro_precision_from_confusion(cm: torch.Tensor) -> float:
    tp = cm.diag().float()
    predicted_positive = cm.sum(dim=0).float()  # стовпці = скільки разів клас c був ПЕРЕДБАЧЕНИЙ
    support = cm.sum(dim=1)  # рядки = скільки разів клас c був ІСТИННИМ
    precision_per_class = torch.where(predicted_positive > 0, tp / predicted_positive.clamp(min=1), torch.zeros_like(tp))
    mask = support > 0
    if mask.sum().item() == 0:
        return 0.0
    return precision_per_class[mask].mean().item()


def evaluate_metrics(
    model: SyscallLSTM,
    loader: DataLoader,
    device: torch.device,
    vocab_size_syscall: int,
    max_batches: int | None = None,
) -> dict[str, float]:

    model.eval()
    total_loss_syscall = 0.0
    total_steps = 0
    cm_syscall = torch.zeros(vocab_size_syscall, vocab_size_syscall, dtype=torch.long)

    with torch.no_grad():
        for batch_idx, (x, y) in enumerate(loader):
            if max_batches is not None and batch_idx >= max_batches:
                break
            x, y = x.to(device), y.to(device)
            logits_syscall = model(x)

            target_syscall = y[..., 0].reshape(-1)
            loss_syscall = F.cross_entropy(logits_syscall.reshape(-1, logits_syscall.size(-1)), target_syscall, reduction="sum")
            total_loss_syscall += loss_syscall.item()
            total_steps += target_syscall.numel()
            pred_syscall = logits_syscall.argmax(dim=-1).reshape(-1)
            _update_confusion(cm_syscall, target_syscall.cpu(), pred_syscall.cpu(), vocab_size_syscall)

    loss_syscall = total_loss_syscall / total_steps
    return {
        "loss_syscall": loss_syscall,
        "perplexity_syscall": float(np.exp(loss_syscall)),
        "precision_syscall": _macro_precision_from_confusion(cm_syscall),
    }


def calibrate_threshold(model: SyscallLSTM, val_loader: DataLoader, device: torch.device) -> float:
    """Поріг тривоги = config.THRESHOLD_PERCENTILE-й перцентиль anomaly
    score (NLL наступного syscall'а) за вікнами НА VAL-СПЛІТІ (held-out
    нормальні дані — модель їх не бачила на train, але вони гарантовано
    без атак)."""
    model.eval()
    scores: list[float] = []
    with torch.no_grad():
        for x, y in val_loader:
            x, y = x.to(device), y.to(device)
            logits_syscall = model(x)
            step_scores = compute_step_scores(logits_syscall, y)
            window_scores = aggregate_window_scores(step_scores, window_agg=config.WINDOW_AGG, window_agg_quantile=config.WINDOW_AGG_QUANTILE)
            scores.extend(window_scores.cpu().tolist())
    return float(np.percentile(scores, config.THRESHOLD_PERCENTILE))


def quick_test_evaluation(
    model: SyscallLSTM, test_loader: DataLoader, threshold: float, device: torch.device
) -> None:

    model.eval()
    steps_parts: list[torch.Tensor] = []
    truth: list[bool] = []
    with torch.no_grad():
        for x, y, window_is_attack in test_loader:
            x, y = x.to(device), y.to(device)
            logits_syscall = model(x)
            step_scores = compute_step_scores(logits_syscall, y)
            steps_parts.append(step_scores.cpu())
            truth.extend(window_is_attack.tolist() if torch.is_tensor(window_is_attack) else list(window_is_attack))

    if not truth:
        print("test-спліт порожній — пропускаю diagnostics-оцінку")
        return

    all_steps = torch.cat(steps_parts, dim=0)
    window_scores = aggregate_window_scores(all_steps, window_agg=config.WINDOW_AGG, window_agg_quantile=config.WINDOW_AGG_QUANTILE).tolist()
    predicted_attack = [s > threshold for s in window_scores]

    print(f"(агрегація вікна: {config.WINDOW_AGG}, score = NLL наступного syscall'а)")
    print(classification_report(truth, predicted_attack, target_names=["Normal", "Attack"], digits=3, zero_division=0))
    if len(set(truth)) == 2:
        auc = roc_auc_score(truth, window_scores)
        print(f"ROC-AUC: {auc:.4f}")
    else:
        print("У test-спліті присутній тільки один клас вікон — ROC-AUC не рахується")


def load_resume_checkpoint(
    service_name: str, checkpoint_path: str, vocab_sizes: dict[str, int], device: torch.device
) -> dict | None:
    if not config.RESUME:
        return None

    if not os.path.exists(checkpoint_path):
        print(f"[{service_name}] config.RESUME=True, але чекпоінт {checkpoint_path} не знайдено — навчання з нуля")
        return None

    checkpoint = torch.load(checkpoint_path, map_location=device)

    if checkpoint["architecture_version"] != ARCHITECTURE_VERSION:
        print(
            f"[{service_name}] УВАГА: чекпоінт збережено архітектурою версії "
            f"{checkpoint['architecture_version']!r}, поточний код — версії {ARCHITECTURE_VERSION} — "
            f"донавчання неможливе, починаю з нуля."
        )
        return None

    if checkpoint["vocab_sizes"] != vocab_sizes:
        print(
            f"[{service_name}] УВАГА: vocab_sizes у чекпоінті {checkpoint['vocab_sizes']} "
            f"не збігається з поточним {vocab_sizes} (змінився train-спліт або config?) — "
            f"донавчання неможливе, починаю з нуля."
        )
        return None

    checkpoint_hparams = ModelHParams.from_checkpoint(checkpoint)
    if checkpoint_hparams.use_arg_count_feature != config.USE_ARG_COUNT_FEATURE:
        print(
            f"[{service_name}] УВАГА: use_arg_count_feature у чекпоінті "
            f"({checkpoint_hparams.use_arg_count_feature}) не збігається з поточним "
            f"config.USE_ARG_COUNT_FEATURE ({config.USE_ARG_COUNT_FEATURE}) — це змінює ширину "
            f"вхідного вектора ознак, донавчання неможливе, починаю з нуля."
        )
        return None

    if checkpoint_hparams != ModelHParams.from_config():
        print(
            f"[{service_name}] гіперпараметри чекпоінта відрізняються від поточного config.py — "
            f"продовжую навчання з АРХІТЕКТУРОЮ З ЧЕКПОІНТА (config.py для архітектури ігнорується "
            f"в цьому запуску): {checkpoint_hparams}"
        )

    return checkpoint


def calibrate_and_evaluate(
    service_name: str,
    model: SyscallLSTM,
    val_loader: DataLoader,
    test_loader: DataLoader | None,
    device: torch.device,
    epoch_label: str | None = None,
) -> float:
    """Калібрує поріг на val і (якщо test_loader доступний) одразу ганяє
    diagnostics-оцінку на test — загальна логіка для "після кожної епохи" та
    "після останньої епохи" гілок у train_one_service."""
    threshold = calibrate_threshold(model, val_loader, device)
    prefix = f"[{service_name}]" + (f" ({epoch_label})" if epoch_label else "")
    print(f"{prefix} поріг тривоги (nll, {config.THRESHOLD_PERCENTILE}-й перцентиль val): {threshold:.4f}")
    if test_loader is not None:
        print(f"{prefix} diagnostics-оцінка на test-спліті:")
        quick_test_evaluation(model, test_loader, threshold, device)
    return threshold


def train_one_service(service_name: str, device: torch.device) -> None:
    print(f"\n=== Сервіс: {service_name} ===")

    vocabs = build_vocab(service_name, use_cache=not config.FORCE_REBUILD_VOCAB)
    vocab_sizes = {name: len(vocab) for name, vocab in vocabs.items()}
    if config.USE_ARG_COUNT_FEATURE:
        vocab_sizes["arg_count"] = config.ARG_COUNT_BUCKETS
    print(f"vocab_sizes={vocab_sizes}")

    X_train, y_train = build_normal_sequences(service_name, vocabs, "train", config.SEQ_LEN, config.SEQ_STEP)
    X_val, y_val = build_normal_sequences(service_name, vocabs, "val", config.SEQ_LEN, config.SEQ_STEP)
    print(f"train-послідовностей: {len(X_train)}  val-послідовностей: {len(X_val)}")

    if len(X_train) == 0 or len(X_val) == 0:
        print(f"[{service_name}] недостатньо даних у train/val (коротше SEQ_LEN+1) — пропускаю")
        return

    train_loader = DataLoader(SequenceDataset(X_train, y_train), batch_size=config.BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(SequenceDataset(X_val, y_val), batch_size=config.BATCH_SIZE, shuffle=False)

    X_test, y_test, window_is_attack = build_test_sequences(service_name, vocabs, config.SEQ_LEN, config.SEQ_LEN)
    test_loader: DataLoader | None = None
    if len(X_test):
        test_loader = DataLoader(EvalSequenceDataset(X_test, y_test, window_is_attack), batch_size=config.BATCH_SIZE, shuffle=False)
    else:
        print(f"[{service_name}] test-спліт порожній або коротший за SEQ_LEN+1 — diagnostics-оцінка недоступна")

    checkpoint_path = os.path.join(config.MODEL_DIR, f"{service_name}.pt")

    resume_checkpoint = load_resume_checkpoint(service_name, checkpoint_path, vocab_sizes, device)
    hparams = ModelHParams.from_checkpoint(resume_checkpoint) if resume_checkpoint is not None else ModelHParams.from_config()

    model = SyscallLSTM(vocab_sizes, hparams=hparams).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.LEARNING_RATE)

    start_epoch = 0
    if resume_checkpoint is not None:
        model.load_state_dict(resume_checkpoint["model_state"])
        if "optimizer_state" in resume_checkpoint:
            optimizer.load_state_dict(resume_checkpoint["optimizer_state"])
        start_epoch = resume_checkpoint["epochs_trained"]
        print(f"[{service_name}] донавчаю з епохи {start_epoch + 1} (чекпоінт: {checkpoint_path})")

    if start_epoch >= config.EPOCHS:
        print(
            f"[{service_name}] чекпоінт вже навчений на {start_epoch} епох >= config.EPOCHS={config.EPOCHS} — "
            f"збільште config.EPOCHS, щоб донавчити далі. Пропускаю навчання, але все одно "
            f"перерахую поріг/diagnostics і перезбережу чекпоінт."
        )

    threshold: float | None = None
    history: dict[str, list[float]] = {
        "epoch": [],
        "train_loss_syscall": [], "val_loss_syscall": [],
        "train_precision_syscall": [], "val_precision_syscall": [],
    }

    for epoch in range(start_epoch, config.EPOCHS):
        model.train()
        total_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            logits_syscall = model(x)
            loss = F.cross_entropy(logits_syscall.reshape(-1, logits_syscall.size(-1)), y[..., 0].reshape(-1))
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        epoch_num = epoch + 1
        running_train_loss = total_loss / len(train_loader)
        is_last_epoch = epoch == config.EPOCHS - 1
        is_metrics_epoch = (epoch_num % config.METRICS_EVAL_EVERY_N_EPOCHS == 0) or is_last_epoch

        if is_metrics_epoch:
            train_metrics = evaluate_metrics(
                model, train_loader, device, vocab_sizes["syscall"],
                max_batches=config.TRAIN_METRICS_MAX_BATCHES,
            )
            val_metrics = evaluate_metrics(model, val_loader, device, vocab_sizes["syscall"])

            print(
                f"[{service_name}] епоха {epoch_num}/{config.EPOCHS}  running_train_loss={running_train_loss:.4f}\n"
                f"  train: loss(syscall)={train_metrics['loss_syscall']:.4f} "
                f"precision(syscall)={train_metrics['precision_syscall']:.3f}\n"
                f"  val:   loss(syscall)={val_metrics['loss_syscall']:.4f} "
                f"precision(syscall)={val_metrics['precision_syscall']:.3f}"
            )

            history["epoch"].append(epoch_num)
            history["train_loss_syscall"].append(train_metrics["loss_syscall"])
            history["val_loss_syscall"].append(val_metrics["loss_syscall"])
            history["train_precision_syscall"].append(train_metrics["precision_syscall"])
            history["val_precision_syscall"].append(val_metrics["precision_syscall"])
        else:
            print(f"[{service_name}] епоха {epoch_num}/{config.EPOCHS}  running_train_loss={running_train_loss:.4f}")

        resource_guard.check_ram(f"{service_name}: кінець епохи {epoch_num}")

        if config.EVAL_TEST_EVERY_EPOCH or is_last_epoch:
            threshold = calibrate_and_evaluate(
                service_name, model, val_loader, test_loader, device,
                epoch_label=f"епоха {epoch_num}/{config.EPOCHS}",
            )

    if history["epoch"]:
        plot_path = plot_training_curves(service_name, history)
        if plot_path:
            print(f"[{service_name}] графік метрик за епохами збережено у {plot_path}")

    if threshold is None:
        threshold = calibrate_and_evaluate(service_name, model, val_loader, test_loader, device)

    os.makedirs(config.MODEL_DIR, exist_ok=True)
    torch.save(
        {
            "architecture_version": ARCHITECTURE_VERSION,
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "epochs_trained": max(start_epoch, config.EPOCHS),
            "vocabs": vocabs,
            "vocab_sizes": vocab_sizes,
            "feature_order": model.feature_order,
            "hparams": model.hparams.to_dict(),
            "seq_len": config.SEQ_LEN,
            "window_agg": config.WINDOW_AGG,
            "window_agg_quantile": config.WINDOW_AGG_QUANTILE,
            "threshold": threshold,
            "service_name": service_name,
        },
        checkpoint_path,
    )
    print(f"[{service_name}] модель збережена у {checkpoint_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--service", help="Навчити тільки один сервіс (за замовчуванням — усі з config.DATASET_ROOT)")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    services = [args.service] if args.service else list_services()
    print(f"Пристрій: {device}")
    print(f"Сервіси: {services}")

    for service_name in services:
        train_one_service(service_name, device)
        gc.collect()
        resource_guard.check_ram(f"після сервісу {service_name}")


if __name__ == "__main__":
    main()