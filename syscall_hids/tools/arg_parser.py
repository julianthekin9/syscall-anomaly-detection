"""Command-line and YAML config argument parsing (modelled on mace/tools/arg_parser.py).

Value priority: CLI > YAML (--config) > parser defaults.
Defaults match the former syscall_hids/config.yaml.
"""

import argparse

import configargparse

WINDOW_AGG_QUANTILE_DEFAULT = 0.90


def str2bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value.lower() in ("yes", "true", "t", "y", "1"):
        return True
    if value.lower() in ("no", "false", "f", "n", "0"):
        return False
    raise argparse.ArgumentTypeError("Boolean value expected.")


def int_or_none(value) -> int | None:
    if value is None or str(value).lower() in ("none", "null"):
        return None
    return int(value)


class _HelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    """Defaults in --help + description (Usage from the docstring) without reformatting."""


def _new_parser(ignore_unknown_config_file_keys: bool, description: str | None = None) -> configargparse.ArgumentParser:
    parser = configargparse.ArgumentParser(
        description=description,
        config_file_parser_class=configargparse.YAMLConfigFileParser,
        formatter_class=_HelpFormatter,
        ignore_unknown_config_file_keys=ignore_unknown_config_file_keys,
    )
    parser.add("--config", type=str, is_config_file=True, help="YAML file with parameters (CLI takes precedence over it)")
    return parser


def _add_bool(group, name: str, default: bool, help: str) -> None:
    # Not store_true: configargparse turns "flag: false" from YAML into "--flag false",
    # and store_true would silently ignore the value
    group.add_argument(name, nargs="?", const=True, type=str2bool, default=default, help=help)


def _add_dir_args(parser, model_dir: bool = True, plots_dir: bool = False, vocab_dir: bool = False, checkpoints_dir: bool = False) -> None:
    group = parser.add_argument_group("Directories")
    group.add_argument("--work_dir", type=str, default=".", help="Base directory; paths not set explicitly are derived from it")
    if model_dir:
        group.add_argument("--model_dir", type=str, default=None, help="Directory for <service>.pt models (None -> {work_dir}/models)")
    if checkpoints_dir:
        group.add_argument("--checkpoints_dir", type=str, default=None,
                           help="Directory for per-epoch checkpoints (None -> {model_dir}/checkpoints)")
    if plots_dir:
        group.add_argument("--plots_dir", type=str, default=None, help="Plots directory (None -> {work_dir}/training_plots)")
    if vocab_dir:
        group.add_argument("--vocab_dir", type=str, default=None, help="Vocab cache directory (None -> {work_dir}/vocabs)")


def _add_ram_args(parser) -> None:
    group = parser.add_argument_group("RAM")
    _add_bool(group, "--ram_guard_enabled", True, "RAM control (resource_guard)")
    group.add_argument("--ram_soft_limit_percent", type=float, default=80.0,
                       help="Above -> gc.collect() + pause + warning, work continues")
    group.add_argument("--ram_hard_limit_percent", type=float, default=92.0,
                       help="Above -> controlled stop (RamLimitExceeded) instead of SIGKILL")
    group.add_argument("--ram_throttle_sleep_sec", type=float, default=2.0, help="Pause after a soft-limit hit, s")
    group.add_argument("--ram_check_every_n_recordings", type=int, default=20,
                       help="How often to check RAM while reading recordings")


def build_default_arg_parser() -> configargparse.ArgumentParser:
    """hids-train parser. An unknown YAML key is an error (a typo is not silently ignored)."""
    parser = _new_parser(ignore_unknown_config_file_keys=False, description="Training the LSTM syscall anomaly detector")

    group = parser.add_argument_group("Data")
    group.add_argument("--dataset_root", type=str, default="./DATASET_LIDDS",
                       help="Dataset root: a single scenario directory or a directory of scenarios")
    group.add_argument("--services", type=str, nargs="+", default=["PHP_CWE-434"], help="Scenarios to train on")

    group = parser.add_argument_group("Features")
    _add_bool(group, "--use_arg_count_feature", True, "Syscall argument count feature")
    group.add_argument("--arg_count_buckets", type=int, default=8,
                       help='arg_count buckets: 0,1,...,6, "7+" — clip(arg_count, 0, arg_count_buckets-1)')
    _add_bool(group, "--force_rebuild_vocab", False, "Rebuild the vocab, ignoring the cache")

    group = parser.add_argument_group("Model")
    group.add_argument("--embed_dim_syscall", type=int, default=16, help="Syscall embedding dimension")
    group.add_argument("--embed_dim_process", type=int, default=8, help="Process embedding dimension")
    group.add_argument("--embed_dim_direction", type=int, default=2, help="Direction embedding dimension")
    group.add_argument("--embed_dim_arg_count", type=int, default=4, help="arg_count embedding dimension (if the feature is enabled)")
    group.add_argument("--hidden_dim", type=int, default=200, help="LSTM hidden state size")
    group.add_argument("--num_layers", type=int, default=2, help="Number of LSTM layers")
    group.add_argument("--dropout", type=float, default=0.2, help="Dropout between LSTM layers (if num_layers > 1)")

    group = parser.add_argument_group("Windows")
    group.add_argument("--seq_len", type=int, default=64, help="Window length (syscall steps)")
    group.add_argument("--seq_step", type=int, default=32, help="Window step on train/val (< seq_len => overlap)")

    group = parser.add_argument_group("Training")
    group.add_argument("--batch_size", type=int, default=32, help="Batch size")
    group.add_argument("--lr", type=float, default=1e-4, help="Learning rate (Adam)")
    group.add_argument("--max_num_epochs", type=int, default=100, help="Number of epochs")
    _add_bool(group, "--restart_latest", False, "Resume training from {model_dir}/<service>.pt if it exists")

    group = parser.add_argument_group("Scoring and threshold")
    group.add_argument("--window_agg", type=str, default="quantile", choices=["quantile", "max", "mean"],
                       help="Aggregation of per-step NLL into a window score")
    group.add_argument("--window_agg_quantile", type=float, default=WINDOW_AGG_QUANTILE_DEFAULT,
                       help="Quantile for window_agg=quantile")
    group.add_argument("--threshold_percentile", type=float, default=99.0,
                       help="Percentile of validation window scores for the threshold")

    group = parser.add_argument_group("Evaluation")
    _add_bool(group, "--eval_test_every_epoch", True, "Calibrate the threshold and evaluate test every epoch")
    group.add_argument("--metrics_eval_every_n_epochs", type=int, default=1, help="How often to compute train/val metrics")
    group.add_argument("--train_metrics_max_batches", type=int_or_none, default=None,
                       help="How many train batches to use for metrics (None: all)")

    _add_dir_args(parser, model_dir=True, plots_dir=True, vocab_dir=True, checkpoints_dir=True)
    _add_ram_args(parser)

    group = parser.add_argument_group("Logging")
    group.add_argument("--name", type=str, default="hids", help="Experiment name, part of the tag of log and metrics files")
    group.add_argument("--seed", type=int, default=123, help="Seed for random, numpy and torch")
    group.add_argument("--log_level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Log level for the console and {tag}.log ({tag}_debug.log records everything)")
    group.add_argument("--log_dir", type=str, default=None, help="Logs directory (None -> {work_dir}/logs)")
    group.add_argument("--results_dir", type=str, default=None, help="JSONL metrics files directory (None -> {work_dir}/results)")
    return parser


def build_eval_arg_parser(description: str | None = None) -> configargparse.ArgumentParser:
    """hids-eval parser. Unknown YAML keys are ignored: the training config can be reused.
    Model and scoring parameters (seq_len, window_agg, threshold, vocabs) come from the checkpoint."""
    parser = _new_parser(ignore_unknown_config_file_keys=True, description=description)
    parser.add_argument("--service", required=True, help="Service name (the same scenario directory as in training)")
    parser.add_argument("--log", help="Path to a specific .sc file to evaluate")
    parser.add_argument("--eval-test-split", action="store_true", help="Evaluate the whole test split of the service (normal+attacks) with quality metrics")
    parser.add_argument("--dataset_root", type=str, default="./DATASET_LIDDS", help="Dataset root (for --eval-test-split)")
    parser.add_argument("--batch_size", type=int, default=32, help="Inference batch size")
    _add_dir_args(parser, model_dir=True, plots_dir=True)
    _add_ram_args(parser)
    return parser


def build_detect_arg_parser(description: str | None = None) -> configargparse.ArgumentParser:
    """hids-detect parser. Unknown YAML keys are ignored. Scoring parameters come from the checkpoint."""
    parser = _new_parser(ignore_unknown_config_file_keys=True, description=description)
    parser.add_argument("--service", default="FLASK", help="Service name: model {model_dir}/<service>.pt and run file prefix")
    parser.add_argument("--container", default="flask-app", help="Docker container whose syscalls are monitored")
    parser.add_argument("--checkpoint", default=None, help="Explicit path to the .pt (default: {model_dir}/<service>.pt)")
    parser.add_argument("--scan-interval", type=float, default=1.0, help="Pause between window checks, s")
    parser.add_argument("--duration", type=float, default=0.0, help="Stop after N seconds (0 = until Ctrl+C)")
    parser.add_argument("--out-dir", default="./realtime_runs", help="Where to save the CSV/plot on exit")
    parser.add_argument("--attack-marker", type=float, default=None,
                         help="For test runs: seconds from start when the attack was launched "
                              "(drawn as a vertical line on the final plot, as in probe_eval)")
    _add_dir_args(parser, model_dir=True)
    return parser
