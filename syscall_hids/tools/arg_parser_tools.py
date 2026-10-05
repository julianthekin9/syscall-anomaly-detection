"""Post-parse argument checking and completion (modelled on mace/tools/arg_parser_tools.py)."""

import logging
import os

import yaml

from syscall_hids.tools.arg_parser import WINDOW_AGG_QUANTILE_DEFAULT


def check_args(args):
    """Derives paths from work_dir and checks consistency; does not change parameter meaning.

    Works with the hids-train, hids-eval and hids-detect parsers: handles only the fields present in args.
    Returns (args, log_messages), where log_messages are (message, logging level) pairs;
    out-of-range values raise ValueError.
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
        raise ValueError(f"window_agg_quantile={args.window_agg_quantile}: must be 0 < window_agg_quantile <= 1")
    if hasattr(args, "threshold_percentile") and not 0 < args.threshold_percentile <= 100:
        raise ValueError(f"threshold_percentile={args.threshold_percentile}: must be 0 < threshold_percentile <= 100")
    if hasattr(args, "seq_step") and not 0 < args.seq_step <= args.seq_len:
        raise ValueError(f"seq_step={args.seq_step}, seq_len={args.seq_len}: must be 0 < seq_step <= seq_len")
    if hasattr(args, "ram_soft_limit_percent") and not args.ram_soft_limit_percent < args.ram_hard_limit_percent:
        raise ValueError(
            f"ram_soft_limit_percent={args.ram_soft_limit_percent} must be less than "
            f"ram_hard_limit_percent={args.ram_hard_limit_percent}"
        )

    if getattr(args, "window_agg", None) == "max" and args.window_agg_quantile != WINDOW_AGG_QUANTILE_DEFAULT:
        log_messages.append((f"window_agg=max: window_agg_quantile={args.window_agg_quantile} is ignored", logging.WARNING))
    if getattr(args, "use_arg_count_feature", True) is False:
        log_messages.append(
            ("use_arg_count_feature=false: embed_dim_arg_count and arg_count_buckets are not used", logging.WARNING)
        )

    return args, log_messages


def save_config_yaml(args, path: str) -> None:
    """Final run configuration as YAML; the file can be passed back to --config."""
    values = {key: value for key, value in vars(args).items() if key != "config"}
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(values, f, sort_keys=False, allow_unicode=True)
