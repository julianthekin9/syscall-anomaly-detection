import logging
import os
import time

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from syscall_hids.data.datasets import SequenceDataset, TestSequenceDataset
from syscall_hids.data.sequences import build_normal_sequences, build_test_sequences
from syscall_hids.data.vocab import build_vocab
from syscall_hids.modules.models import ARCHITECTURE_VERSION, ModelHParams, SyscallLSTM
from syscall_hids.tools import resource_guard
from syscall_hids.tools.arg_parser_tools import save_config_yaml
from syscall_hids.tools.evaluation import calibrate_and_evaluate, evaluate_metrics
from syscall_hids.tools.utils import MetricsLogger
from syscall_hids.tools.visualization import plot_training_curves

def load_resume_checkpoint(
    service_name: str, checkpoint_path: str, vocab_sizes: dict[str, int], device: torch.device, args
) -> dict | None:
    if not args.restart_latest:
        return None

    if not os.path.exists(checkpoint_path):
        logging.warning(f"[{service_name}] restart_latest=True, але чекпоінт {checkpoint_path} не знайдено — навчання з нуля")
        return None

    checkpoint = torch.load(checkpoint_path, map_location=device)

    if checkpoint["architecture_version"] != ARCHITECTURE_VERSION:
        logging.warning(
            f"[{service_name}] УВАГА: чекпоінт архітектури версії {checkpoint['architecture_version']!r}, "
            f"поточний код — {ARCHITECTURE_VERSION} — донавчання неможливе, починаю з нуля."
        )
        return None

    if checkpoint["vocab_sizes"] != vocab_sizes:
        logging.warning(
            f"[{service_name}] УВАГА: vocab_sizes у чекпоінті {checkpoint['vocab_sizes']} "
            f"не збігається з поточним {vocab_sizes} — донавчання неможливе, починаю з нуля."
        )
        return None

    checkpoint_hparams = ModelHParams.from_checkpoint(checkpoint)
    if checkpoint_hparams.use_arg_count_feature != args.use_arg_count_feature:
        logging.warning(
            f"[{service_name}] УВАГА: use_arg_count_feature у чекпоінті не збігається з аргументами — "
            f"донавчання неможливе, починаю з нуля."
        )
        return None

    if checkpoint_hparams != ModelHParams.from_args(args):
        logging.warning(
            f"[{service_name}] гіперпараметри чекпоінта відрізняються від аргументів — "
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
    args,
    git_commit: str | None = None,
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
        "seq_len": args.seq_len,
        "window_agg": args.window_agg,
        "window_agg_quantile": args.window_agg_quantile,
        "threshold": threshold,
        "service_name": service_name,
        "train_args": vars(args),  # підсумкова конфігурація запуску (після check_args)
        "git_commit": git_commit,
    }


def save_epoch_checkpoint(
    service_name: str,
    epoch_num: int,
    model: SyscallLSTM,
    optimizer: torch.optim.Optimizer,
    vocabs: dict,
    vocab_sizes: dict,
    threshold: float | None,
    args,
    git_commit: str | None = None,
) -> str:
    service_ckpt_dir = os.path.join(args.checkpoints_dir, service_name)
    os.makedirs(service_ckpt_dir, exist_ok=True)
    path = os.path.join(service_ckpt_dir, f"{service_name}_epoch_{epoch_num:03d}.pt")
    torch.save(
        build_checkpoint(service_name, model, optimizer, vocabs, vocab_sizes, epoch_num, threshold, args, git_commit),
        path,
    )
    return path


def _log_threshold(metrics_logger: MetricsLogger, epoch: int, threshold: float, args) -> None:
    metrics_logger.log({
        "mode": "threshold", "epoch": epoch, "threshold": threshold, "percentile": args.threshold_percentile,
        "window_agg": args.window_agg, "window_agg_quantile": args.window_agg_quantile,
    })


def train_one_service(service_name: str, device: torch.device, args, git_commit: str | None = None) -> None:
    metrics_logger = MetricsLogger(
        args.results_dir, f"{args.name}_{service_name}_run-{args.seed}_train", append=args.restart_latest
    )

    logging.info("===========LOADING INPUT DATA===========")
    logging.info(f"\n=== Сервіс: {service_name} ===")

    vocabs = build_vocab(service_name, args.dataset_root, args.vocab_dir, use_cache=not args.force_rebuild_vocab)
    vocab_sizes = {name: len(vocab) for name, vocab in vocabs.items()}
    if args.use_arg_count_feature:
        vocab_sizes["arg_count"] = args.arg_count_buckets
    logging.info(f"vocab_sizes={vocab_sizes}")

    data_kwargs = dict(
        dataset_root=args.dataset_root,
        use_arg_count_feature=args.use_arg_count_feature,
        arg_count_buckets=args.arg_count_buckets,
        ram_check_every_n_recordings=args.ram_check_every_n_recordings,
    )
    X_train, y_train = build_normal_sequences(service_name, vocabs, "train", args.seq_len, args.seq_step, **data_kwargs)
    X_val, y_val = build_normal_sequences(service_name, vocabs, "val", args.seq_len, args.seq_step, **data_kwargs)
    logging.info(f"train-послідовностей: {len(X_train)}  val-послідовностей: {len(X_val)}")

    if len(X_train) == 0 or len(X_val) == 0:
        logging.warning(f"[{service_name}] недостатньо даних у train/val — пропускаю")
        return

    train_loader = DataLoader(SequenceDataset(X_train, y_train), batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(SequenceDataset(X_val, y_val), batch_size=args.batch_size, shuffle=False)

    X_test, y_test, window_is_attack = build_test_sequences(service_name, vocabs, args.seq_len, args.seq_len, **data_kwargs)
    test_loader: DataLoader | None = None
    if len(X_test):
        test_loader = DataLoader(
            TestSequenceDataset(X_test, y_test, window_is_attack),
            batch_size=args.batch_size, shuffle=False,
        )
        logging.info(
            f"test-вікон: {len(X_test)}, з них атакуючих: {int(window_is_attack.sum())} "
            f"({window_is_attack.mean():.1%})"
        )
    else:
        logging.warning(f"[{service_name}] test-спліт порожній — diagnostics-оцінка недоступна")

    checkpoint_path = os.path.join(args.model_dir, f"{service_name}.pt")

    resume_checkpoint = load_resume_checkpoint(service_name, checkpoint_path, vocab_sizes, device, args)
    hparams = (
        ModelHParams.from_checkpoint(resume_checkpoint)
        if resume_checkpoint is not None
        else ModelHParams.from_args(args)
    )

    model = SyscallLSTM(vocab_sizes, hparams=hparams).to(device)
    logging.info("===========MODEL DETAILS===========")
    logging.info(f"hparams: {hparams}")
    logging.info(f"ARCHITECTURE_VERSION: {ARCHITECTURE_VERSION}")
    logging.info(f"Кількість параметрів, що навчаються: {sum(p.numel() for p in model.parameters() if p.requires_grad)}")

    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    logging.info("===========OPTIMIZER INFORMATION===========")
    logging.info(f"Оптимізатор: Adam, lr={args.lr}")
    logging.info(f"batch_size={args.batch_size}, max_num_epochs={args.max_num_epochs}, кроків на епоху: {len(train_loader)}")

    start_epoch = 0
    if resume_checkpoint is not None:
        model.load_state_dict(resume_checkpoint["model_state"])
        if "optimizer_state" in resume_checkpoint:
            optimizer.load_state_dict(resume_checkpoint["optimizer_state"])
        start_epoch = resume_checkpoint["epochs_trained"]
        logging.info(f"[{service_name}] донавчаю з епохи {start_epoch + 1} (чекпоінт: {checkpoint_path})")

    if start_epoch >= args.max_num_epochs:
        logging.warning(
            f"[{service_name}] чекпоінт вже навчений на {start_epoch} епох >= max_num_epochs={args.max_num_epochs} — "
            f"збільште --max_num_epochs, щоб донавчити далі."
        )

    threshold: float | None = None
    test_metrics: dict | None = None
    history: dict[str, list[float]] = {
        "epoch": [],
        "train_loss_syscall": [], "val_loss_syscall": [],
        "train_precision_syscall": [], "val_precision_syscall": [],
    }

    logging.info("===========TRAINING===========")
    step = start_epoch * len(train_loader)
    for epoch in range(start_epoch, args.max_num_epochs):
        epoch_num = epoch + 1
        epoch_start = time.perf_counter()
        model.train()
        total_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            logits_syscall = model(x)
            loss = F.cross_entropy(logits_syscall.reshape(-1, logits_syscall.size(-1)), y[..., 0].reshape(-1))
            loss.backward()
            optimizer.step()
            loss_value = loss.item()
            total_loss += loss_value
            step += 1
            metrics_logger.log({
                "mode": "opt", "epoch": epoch_num, "step": step, "loss": loss_value,
                "lr": optimizer.param_groups[0]["lr"],
            })

        running_train_loss = total_loss / len(train_loader)
        is_last_epoch = epoch == args.max_num_epochs - 1
        is_metrics_epoch = (epoch_num % args.metrics_eval_every_n_epochs == 0) or is_last_epoch

        if is_metrics_epoch:
            train_metrics = evaluate_metrics(
                model, train_loader, device, vocab_sizes["syscall"],
                max_batches=args.train_metrics_max_batches,
            )
            val_metrics = evaluate_metrics(model, val_loader, device, vocab_sizes["syscall"])
            epoch_time = time.perf_counter() - epoch_start

            logging.debug(
                f"[{service_name}] епоха {epoch_num}/{args.max_num_epochs}; поточне значення функції втрат на навчальній виборці = {running_train_loss:.4f}\n"
                f"  Навчальна вибірка: Loss = {train_metrics['loss_syscall']:.4f} "
                f"Precision = {train_metrics['precision_syscall']:.3f}\n"
                f"  Валідаційна вибірка: Loss = {val_metrics['loss_syscall']:.4f} "
                f"Precision = {val_metrics['precision_syscall']:.3f}"
            )
            logging.info(
                f"Epoch {epoch_num}/{args.max_num_epochs}: train_loss={running_train_loss:.4f}, "
                f"val_nll={val_metrics['loss_syscall']:.4f}, macro_precision={val_metrics['precision_syscall']:.3f}, "
                f"time={epoch_time:.1f}s"
            )
            for split, split_metrics in (("train", train_metrics), ("val", val_metrics)):
                metrics_logger.log({
                    "mode": "eval", "epoch": epoch_num, "split": split,
                    "loss": split_metrics["loss_syscall"], "perplexity": split_metrics["perplexity_syscall"],
                    "precision": split_metrics["precision_syscall"], "time": epoch_time,
                })

            history["epoch"].append(epoch_num)
            history["train_loss_syscall"].append(train_metrics["loss_syscall"])
            history["val_loss_syscall"].append(val_metrics["loss_syscall"])
            history["train_precision_syscall"].append(train_metrics["precision_syscall"])
            history["val_precision_syscall"].append(val_metrics["precision_syscall"])
        else:
            epoch_time = time.perf_counter() - epoch_start
            logging.debug(
                f"[{service_name}] епоха {epoch_num}/{args.max_num_epochs}   "
                f"поточне значення функції втрат на навчальній виборці = {running_train_loss:.4f}"
            )
            logging.info(
                f"Epoch {epoch_num}/{args.max_num_epochs}: train_loss={running_train_loss:.4f}, time={epoch_time:.1f}s"
            )

        resource_guard.check_ram(f"{service_name}: кінець епохи {epoch_num}")
        metrics_logger.log({
            "mode": "ram", "epoch": epoch_num,
            "rss_gb": resource_guard.process_rss_gb(), "ram_percent": resource_guard.ram_usage_percent(),
        })

        if args.eval_test_every_epoch or is_last_epoch:
            # остання епоха — це і є підсумкова модель, тож її ROC-крива зберігається ще й як "final"
            roc_tags = (f"epoch{epoch_num:03d}",) + (("final",) if is_last_epoch else ())
            threshold, test_metrics = calibrate_and_evaluate(
                service_name, model, val_loader, test_loader, device, roc_tags, args,
                epoch_label=f"епоха {epoch_num}/{args.max_num_epochs}",
            )
            _log_threshold(metrics_logger, epoch_num, threshold, args)
            if test_metrics is not None:
                metrics_logger.log({"mode": "test", "epoch": epoch_num, **test_metrics})

        ckpt_path = save_epoch_checkpoint(
            service_name, epoch_num, model, optimizer,
            vocabs, vocab_sizes, threshold, args, git_commit,
        )
        logging.debug(f"[{service_name}] чекпоінт епохи {epoch_num} збережено у {ckpt_path}")

    if history["epoch"]:
        plot_path = plot_training_curves(service_name, history, args.plots_dir)
        if plot_path:
            logging.info(f"[{service_name}] графік метрик за епохами збережено у {plot_path}")

    epochs_trained = max(start_epoch, args.max_num_epochs)
    if threshold is None:
        threshold, test_metrics = calibrate_and_evaluate(
            service_name, model, val_loader, test_loader, device, ("final",), args
        )
        _log_threshold(metrics_logger, epochs_trained, threshold, args)
        if test_metrics is not None:
            metrics_logger.log({"mode": "test", "epoch": epochs_trained, **test_metrics})

    os.makedirs(args.model_dir, exist_ok=True)
    torch.save(
        build_checkpoint(
            service_name, model, optimizer, vocabs, vocab_sizes,
            epochs_trained=epochs_trained,
            threshold=threshold,
            args=args,
            git_commit=git_commit,
        ),
        checkpoint_path,
    )

    logging.info("===========RESULTS===========")
    logging.info(f"[{service_name}] поріг тривоги: {threshold:.4f}")
    if test_metrics is not None:
        auc = "n/a" if test_metrics["auc"] is None else f"{test_metrics['auc']:.4f}"
        attack = test_metrics["attack"]
        logging.info(
            f"[{service_name}] test: ROC-AUC={auc}, accuracy={test_metrics['accuracy']:.3f}, "
            f"attack precision={attack['precision']:.3f} recall={attack['recall']:.3f} f1={attack['f1']:.3f}"
        )
    logging.info(f"[{service_name}] модель збережена у {checkpoint_path}")
    config_path = os.path.join(args.model_dir, f"{service_name}_config.yaml")
    save_config_yaml(args, config_path)
    logging.info(f"[{service_name}] конфігурацію запуску збережено у {config_path} (можна передати в --config)")
    logging.info(f"[{service_name}] метрики JSONL: {metrics_logger.path}")
