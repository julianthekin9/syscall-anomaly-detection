import os

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from syscall_hids import config
from syscall_hids.data.datasets import SequenceDataset, TestSequenceDataset
from syscall_hids.data.sequences import build_normal_sequences, build_test_sequences
from syscall_hids.data.vocab import build_vocab
from syscall_hids.modules.models import ARCHITECTURE_VERSION, ModelHParams, SyscallLSTM
from syscall_hids.tools import resource_guard
from syscall_hids.tools.evaluation import calibrate_and_evaluate, evaluate_metrics
from syscall_hids.tools.visualization import plot_training_curves

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
            f"[{service_name}] УВАГА: чекпоінт архітектури версії {checkpoint['architecture_version']!r}, "
            f"поточний код — {ARCHITECTURE_VERSION} — донавчання неможливе, починаю з нуля."
        )
        return None

    if checkpoint["vocab_sizes"] != vocab_sizes:
        print(
            f"[{service_name}] УВАГА: vocab_sizes у чекпоінті {checkpoint['vocab_sizes']} "
            f"не збігається з поточним {vocab_sizes} — донавчання неможливе, починаю з нуля."
        )
        return None

    checkpoint_hparams = ModelHParams.from_checkpoint(checkpoint)
    if checkpoint_hparams.use_arg_count_feature != config.USE_ARG_COUNT_FEATURE:
        print(
            f"[{service_name}] УВАГА: use_arg_count_feature у чекпоінті не збігається з config — "
            f"донавчання неможливе, починаю з нуля."
        )
        return None

    if checkpoint_hparams != ModelHParams.from_config():
        print(
            f"[{service_name}] гіперпараметри чекпоінта відрізняються від config.py — "
            f"використовую архітектуру з чекпоінта: {checkpoint_hparams}"
        )

    return checkpoint


def build_checkpoint(
    service_name: str,
    model: SyscallLSTM,
    optimizer: torch.optim.Optimizer,
    vocabs: dict,
    vocab_sizes: dict,
    epochs_trained: int,
    threshold: float | None,
) -> dict:
    return {
        "architecture_version": ARCHITECTURE_VERSION,
        "model_state": model.state_dict(),
        "optimizer_state": optimizer.state_dict(),
        "epochs_trained": epochs_trained,
        "vocabs": vocabs,
        "vocab_sizes": vocab_sizes,
        "feature_order": model.feature_order,
        "hparams": model.hparams.to_dict(),
        "seq_len": config.SEQ_LEN,
        "window_agg": config.WINDOW_AGG,
        "window_agg_quantile": config.WINDOW_AGG_QUANTILE,
        "threshold": threshold,
        "service_name": service_name,
    }


def save_epoch_checkpoint(
    service_name: str,
    epoch_num: int,
    model: SyscallLSTM,
    optimizer: torch.optim.Optimizer,
    vocabs: dict,
    vocab_sizes: dict,
    threshold: float | None,
) -> str:
    service_ckpt_dir = os.path.join(config.CHECKPOINT_DIR, service_name)
    os.makedirs(service_ckpt_dir, exist_ok=True)
    path = os.path.join(service_ckpt_dir, f"{service_name}_epoch_{epoch_num:03d}.pt")
    torch.save(
        build_checkpoint(service_name, model, optimizer, vocabs, vocab_sizes, epoch_num, threshold),
        path,
    )
    return path


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
        print(f"[{service_name}] недостатньо даних у train/val — пропускаю")
        return

    train_loader = DataLoader(SequenceDataset(X_train, y_train), batch_size=config.BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(SequenceDataset(X_val, y_val), batch_size=config.BATCH_SIZE, shuffle=False)

    X_test, y_test, window_is_attack = build_test_sequences(service_name, vocabs, config.SEQ_LEN, config.SEQ_LEN)
    test_loader: DataLoader | None = None
    if len(X_test):
        test_loader = DataLoader(
            TestSequenceDataset(X_test, y_test, window_is_attack),
            batch_size=config.BATCH_SIZE, shuffle=False,
        )
    else:
        print(f"[{service_name}] test-спліт порожній — diagnostics-оцінка недоступна")

    checkpoint_path = os.path.join(config.MODEL_DIR, f"{service_name}.pt")

    resume_checkpoint = load_resume_checkpoint(service_name, checkpoint_path, vocab_sizes, device)
    hparams = (
        ModelHParams.from_checkpoint(resume_checkpoint)
        if resume_checkpoint is not None
        else ModelHParams.from_config()
    )

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
            f"збільште config.EPOCHS, щоб донавчити далі."
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
                f"[{service_name}] епоха {epoch_num}/{config.EPOCHS}; поточне значення функції втрат на навчальній виборці = {running_train_loss:.4f}\n"
                f"  Навчальна вибірка: Loss = {train_metrics['loss_syscall']:.4f} "
                f"Precision = {train_metrics['precision_syscall']:.3f}\n"
                f"  Валідаційна вибірка: Loss = {val_metrics['loss_syscall']:.4f} "
                f"Precision = {val_metrics['precision_syscall']:.3f}"
            )

            history["epoch"].append(epoch_num)
            history["train_loss_syscall"].append(train_metrics["loss_syscall"])
            history["val_loss_syscall"].append(val_metrics["loss_syscall"])
            history["train_precision_syscall"].append(train_metrics["precision_syscall"])
            history["val_precision_syscall"].append(val_metrics["precision_syscall"])
        else:
            print(
                f"[{service_name}] епоха {epoch_num}/{config.EPOCHS}   "
                f"поточне значення функції втрат на навчальній виборці = {running_train_loss:.4f}"
            )

        resource_guard.check_ram(f"{service_name}: кінець епохи {epoch_num}")

        if config.EVAL_TEST_EVERY_EPOCH or is_last_epoch:
            threshold = calibrate_and_evaluate(
                service_name, model, val_loader, test_loader, device,
                epoch_label=f"епоха {epoch_num}/{config.EPOCHS}",
            )

        ckpt_path = save_epoch_checkpoint(
            service_name, epoch_num, model, optimizer,
            vocabs, vocab_sizes, threshold,
        )
        print(f"[{service_name}] чекпоінт епохи {epoch_num} збережено у {ckpt_path}")

    if history["epoch"]:
        plot_path = plot_training_curves(service_name, history)
        if plot_path:
            print(f"[{service_name}] графік метрик за епохами збережено у {plot_path}")

    if threshold is None:
        threshold = calibrate_and_evaluate(service_name, model, val_loader, test_loader, device)

    os.makedirs(config.MODEL_DIR, exist_ok=True)
    torch.save(
        build_checkpoint(
            service_name, model, optimizer, vocabs, vocab_sizes,
            epochs_trained=max(start_epoch, config.EPOCHS),
            threshold=threshold,
        ),
        checkpoint_path,
    )
    print(f"[{service_name}] модель збережена у {checkpoint_path}")
