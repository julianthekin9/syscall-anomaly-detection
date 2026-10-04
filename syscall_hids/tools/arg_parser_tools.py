"""Перевірка та доповнення аргументів після розбору (за зразком mace/tools/arg_parser_tools.py)."""

import logging
import os

import yaml

from syscall_hids.tools.arg_parser import WINDOW_AGG_QUANTILE_DEFAULT


def check_args(args):
    """Виводить шляхи з work_dir і перевіряє узгодженість; смисл параметрів не змінює.

    Працює з парсерами hids-train, hids-eval і hids-detect: обробляє лише ті поля, які є в args.
    Повертає (args, log_messages), log_messages — пари (повідомлення, рівень logging);
    порушення діапазонів — ValueError.
    """
    log_messages: list[tuple[str, int]] = []

    if getattr(args, "model_dir", "") is None:
        args.model_dir = os.path.join(args.work_dir, "models")
    if getattr(args, "checkpoints_dir", "") is None:
        args.checkpoints_dir = os.path.join(args.model_dir, "checkpoints")
    if getattr(args, "plots_dir", "") is None:
        args.plots_dir = os.path.join(args.work_dir, "training_plots")
    if getattr(args, "vocab_dir", "") is None:
        args.vocab_dir = os.path.join(args.work_dir, "vocabs")
    if getattr(args, "log_dir", "") is None:
        args.log_dir = os.path.join(args.work_dir, "logs")
    if getattr(args, "results_dir", "") is None:
        args.results_dir = os.path.join(args.work_dir, "results")

    if hasattr(args, "window_agg_quantile") and not 0 < args.window_agg_quantile <= 1:
        raise ValueError(f"window_agg_quantile={args.window_agg_quantile}: потрібно 0 < window_agg_quantile <= 1")
    if hasattr(args, "threshold_percentile") and not 0 < args.threshold_percentile <= 100:
        raise ValueError(f"threshold_percentile={args.threshold_percentile}: потрібно 0 < threshold_percentile <= 100")
    if hasattr(args, "seq_step") and not 0 < args.seq_step <= args.seq_len:
        raise ValueError(f"seq_step={args.seq_step}, seq_len={args.seq_len}: потрібно 0 < seq_step <= seq_len")
    if hasattr(args, "ram_soft_limit_percent") and not args.ram_soft_limit_percent < args.ram_hard_limit_percent:
        raise ValueError(
            f"ram_soft_limit_percent={args.ram_soft_limit_percent} має бути менше "
            f"ram_hard_limit_percent={args.ram_hard_limit_percent}"
        )

    if getattr(args, "window_agg", None) == "max" and args.window_agg_quantile != WINDOW_AGG_QUANTILE_DEFAULT:
        log_messages.append((f"window_agg=max: window_agg_quantile={args.window_agg_quantile} ігнорується", logging.WARNING))
    if getattr(args, "use_arg_count_feature", True) is False:
        log_messages.append(
            ("use_arg_count_feature=false: embed_dim_arg_count і arg_count_buckets не використовуються", logging.WARNING)
        )

    return args, log_messages


def save_config_yaml(args, path: str) -> None:
    """Підсумкова конфігурація запуску в YAML; файл можна передати назад у --config."""
    values = {key: value for key, value in vars(args).items() if key != "config"}
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(values, f, sort_keys=False, allow_unicode=True)
