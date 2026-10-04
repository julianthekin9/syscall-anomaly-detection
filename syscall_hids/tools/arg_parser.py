"""Розбір аргументів командного рядка та YAML-конфігу (за зразком mace/tools/arg_parser.py).

Пріоритет значень: CLI > YAML (--config) > значення за замовчуванням у парсері.
Значення за замовчуванням дорівнюють колишньому syscall_hids/config.yaml.
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
    """Значення за замовчуванням у --help + опис (Usage з docstring) без переформатування."""


def _new_parser(ignore_unknown_config_file_keys: bool, description: str | None = None) -> configargparse.ArgumentParser:
    parser = configargparse.ArgumentParser(
        description=description,
        config_file_parser_class=configargparse.YAMLConfigFileParser,
        formatter_class=_HelpFormatter,
        ignore_unknown_config_file_keys=ignore_unknown_config_file_keys,
    )
    parser.add("--config", type=str, is_config_file=True, help="YAML-файл з параметрами (CLI має пріоритет над ним)")
    return parser


def _add_bool(group, name: str, default: bool, help: str) -> None:
    # Не store_true: configargparse перетворює "flag: false" з YAML на "--flag false",
    # і store_true мовчки проігнорував би значення
    group.add_argument(name, nargs="?", const=True, type=str2bool, default=default, help=help)


def _add_dir_args(parser, model_dir: bool = True, plots_dir: bool = False, vocab_dir: bool = False, checkpoints_dir: bool = False) -> None:
    group = parser.add_argument_group("Директорії")
    group.add_argument("--work_dir", type=str, default=".", help="Базова тека; з неї виводяться шляхи, не задані явно")
    if model_dir:
        group.add_argument("--model_dir", type=str, default=None, help="Тека моделей <сервіс>.pt (None -> {work_dir}/models)")
    if checkpoints_dir:
        group.add_argument("--checkpoints_dir", type=str, default=None,
                           help="Тека поепохових чекпоінтів (None -> {model_dir}/checkpoints)")
    if plots_dir:
        group.add_argument("--plots_dir", type=str, default=None, help="Тека графіків (None -> {work_dir}/training_plots)")
    if vocab_dir:
        group.add_argument("--vocab_dir", type=str, default=None, help="Тека кешу словників (None -> {work_dir}/vocabs)")


def _add_ram_args(parser) -> None:
    group = parser.add_argument_group("RAM")
    _add_bool(group, "--ram_guard_enabled", True, "Контроль RAM (resource_guard)")
    group.add_argument("--ram_soft_limit_percent", type=float, default=80.0,
                       help="Вище -> gc.collect() + пауза + попередження, робота продовжується")
    group.add_argument("--ram_hard_limit_percent", type=float, default=92.0,
                       help="Вище -> контрольована зупинка (RamLimitExceeded) замість SIGKILL")
    group.add_argument("--ram_throttle_sleep_sec", type=float, default=2.0, help="Пауза після м'якого спрацювання, с")
    group.add_argument("--ram_check_every_n_recordings", type=int, default=20,
                       help="Як часто перевіряти RAM під час читання записів")


def build_default_arg_parser() -> configargparse.ArgumentParser:
    """Парсер hids-train. Невідомий ключ у YAML — помилка (одруківка не ігнорується мовчки)."""
    parser = _new_parser(ignore_unknown_config_file_keys=False, description="Навчання LSTM-детектора аномалій syscall'ів")

    group = parser.add_argument_group("Дані")
    group.add_argument("--dataset_root", type=str, default="./DATASET_LIDDS",
                       help="Корінь датасету: тека одного сценарію або тека зі сценаріями")
    group.add_argument("--services", type=str, nargs="+", default=["PHP_CWE-434"], help="Сценарії для навчання")

    group = parser.add_argument_group("Ознаки")
    _add_bool(group, "--use_arg_count_feature", True, "Ознака кількості аргументів syscall'а")
    group.add_argument("--arg_count_buckets", type=int, default=8,
                       help='Кошики arg_count: 0,1,...,6, "7+" — clip(arg_count, 0, arg_count_buckets-1)')
    _add_bool(group, "--force_rebuild_vocab", False, "Перебудувати словник, ігноруючи кеш")

    group = parser.add_argument_group("Модель")
    group.add_argument("--embed_dim_syscall", type=int, default=16, help="Розмірність ембедингу syscall")
    group.add_argument("--embed_dim_process", type=int, default=8, help="Розмірність ембедингу процесу")
    group.add_argument("--embed_dim_direction", type=int, default=2, help="Розмірність ембедингу напряму")
    group.add_argument("--embed_dim_arg_count", type=int, default=4, help="Розмірність ембедингу arg_count (якщо ознака увімкнена)")
    group.add_argument("--hidden_dim", type=int, default=200, help="Розмір прихованого стану LSTM")
    group.add_argument("--num_layers", type=int, default=2, help="Кількість шарів LSTM")
    group.add_argument("--dropout", type=float, default=0.2, help="Dropout між шарами LSTM (якщо num_layers > 1)")

    group = parser.add_argument_group("Вікна")
    group.add_argument("--seq_len", type=int, default=64, help="Довжина вікна (кроків syscall)")
    group.add_argument("--seq_step", type=int, default=32, help="Крок вікна на train/val (< seq_len => перекриття)")

    group = parser.add_argument_group("Навчання")
    group.add_argument("--batch_size", type=int, default=32, help="Розмір батча")
    group.add_argument("--lr", type=float, default=1e-4, help="Learning rate (Adam)")
    group.add_argument("--max_num_epochs", type=int, default=100, help="Кількість епох")
    _add_bool(group, "--restart_latest", False, "Донавчати з {model_dir}/<сервіс>.pt, якщо він є")

    group = parser.add_argument_group("Скоринг і поріг")
    group.add_argument("--window_agg", type=str, default="quantile", choices=["quantile", "max", "mean"],
                       help="Агрегація покрокових NLL в оцінку вікна")
    group.add_argument("--window_agg_quantile", type=float, default=WINDOW_AGG_QUANTILE_DEFAULT,
                       help="Квантиль для window_agg=quantile")
    group.add_argument("--threshold_percentile", type=float, default=99.0,
                       help="Перцентиль віконних оцінок на validation для порогу")

    group = parser.add_argument_group("Оцінка")
    _add_bool(group, "--eval_test_every_epoch", True, "Калібрувати поріг і оцінювати test на кожній епосі")
    group.add_argument("--metrics_eval_every_n_epochs", type=int, default=1, help="Як часто рахувати метрики train/val")
    group.add_argument("--train_metrics_max_batches", type=int_or_none, default=None,
                       help="Скільки батчів train брати для метрик (None — усі)")

    _add_dir_args(parser, model_dir=True, plots_dir=True, vocab_dir=True, checkpoints_dir=True)
    _add_ram_args(parser)
    return parser


def build_eval_arg_parser(description: str | None = None) -> configargparse.ArgumentParser:
    """Парсер hids-eval. Невідомі ключі YAML ігноруються: підходить той самий конфіг, що й для навчання.
    Параметри моделі й скорингу (seq_len, window_agg, поріг, словники) беруться з чекпоінта."""
    parser = _new_parser(ignore_unknown_config_file_keys=True, description=description)
    parser.add_argument("--service", required=True, help="Имя сервиса (та же папка сценария, что при обучении)")
    parser.add_argument("--log", help="Путь к конкретному .sc-файлу для оценки")
    parser.add_argument("--eval-test-split", action="store_true", help="Оценить весь test-сплит сервиса (норма+атаки) с метриками качества")
    parser.add_argument("--dataset_root", type=str, default="./DATASET_LIDDS", help="Корінь датасету (для --eval-test-split)")
    parser.add_argument("--batch_size", type=int, default=32, help="Розмір батча інференсу")
    _add_dir_args(parser, model_dir=True, plots_dir=True)
    _add_ram_args(parser)
    return parser


def build_detect_arg_parser(description: str | None = None) -> configargparse.ArgumentParser:
    """Парсер hids-detect. Невідомі ключі YAML ігноруються. Параметри скорингу — з чекпоінта."""
    parser = _new_parser(ignore_unknown_config_file_keys=True, description=description)
    parser.add_argument("--service", default="FLASK", help="Имя сервиса: модель {model_dir}/<service>.pt и префикс файлов прогона")
    parser.add_argument("--container", default="flask-app", help="Docker-контейнер, syscall'ы которого отслеживаются")
    parser.add_argument("--checkpoint", default=None, help="Явный путь к .pt (по умолчанию — {model_dir}/<service>.pt)")
    parser.add_argument("--scan-interval", type=float, default=1.0, help="Пауза между проверками окна, сек")
    parser.add_argument("--duration", type=float, default=0.0, help="Остановиться через N секунд (0 = до Ctrl+C)")
    parser.add_argument("--out-dir", default="./realtime_runs", help="Куда сохранять CSV/график по завершении")
    parser.add_argument("--attack-marker", type=float, default=None,
                         help="Для тестовых прогонов: секунды от старта, когда была инициирована атака "
                              "(рисуется вертикальной линией на итоговом графике, как в probe_eval)")
    _add_dir_args(parser, model_dir=True)
    return parser
