# Этап 3. Конфиг в YAML + CLI с переопределением (как в mace-torch)

Задание для Claude Code. Выполняется после этапа 2б (`docs/STAGE2B_FIXES.md`). Предусловие: `pytest tests/` зелёный, и в нём есть эталон мини-обучения (`tests/test_train_regression.py`). Если нет, остановись и скажи мне.

## Исходное состояние (коммит cdf9d5b)
Параметры уже вынесены в корневой `config.yaml`. `syscall_hids/config.py` читает его при импорте в атрибуты `config.X`, все ключи обязательны, и там же лежат константы формата трассы. YAML уже есть, но глобальный модуль `config` остался, а чтение файла при импорте зависит от текущей папки (в установленном пакете и в Colab это ломается).

## Цель

1. `syscall_hids/config.py` (глобальный модуль) и чтение `config.yaml` при импорте исчезают. Все параметры задаются через CLI-аргументы.
2. `hids-train --config configs/<эксперимент>.yaml` берёт параметры из YAML. Корневой `config.yaml` переезжает (`git mv`) в `configs/php_cwe_434.yaml` и становится обычным `--config`-файлом.
3. Любой параметр можно переопределить в командной строке, и CLI сильнее YAML: `hids-train --config configs/flask.yaml --lr 5e-4 --max_num_epochs 20`.
4. Приоритет: **CLI > YAML > значение по умолчанию в парсере**.
5. Значения по умолчанию в парсере в точности равны текущим значениям из `config.yaml` (коммит cdf9d5b), поэтому `hids-train --config configs/php_cwe_434.yaml` ведёт себя как сейчас `hids-train`. Регрессионные тесты обязаны остаться зелёными без перегенерации эталона.

## Как это сделано в mace-torch (образец)

`mace/tools/arg_parser.py`:
```python
def build_default_arg_parser() -> argparse.ArgumentParser:
    import configargparse
    parser = configargparse.ArgumentParser(
        config_file_parser_class=configargparse.YAMLConfigFileParser,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add("--config", type=str, is_config_file=True, help="config file to aggregate options")
    parser.add_argument("--work_dir", type=str, default=".", help="...")
    parser.add_argument("--model_dir", type=str, default=None, help="...")   # None -> выводится из work_dir
    ...
    return parser

def str2bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() in ("yes", "true", "t", "y", "1"):
        return True
    if value.lower() in ("no", "false", "f", "n", "0"):
        return False
    raise argparse.ArgumentTypeError("Boolean value expected.")
```
Булевы флаги в mace объявлены как `nargs="?", const=True, type=str2bool`, а НЕ `store_true`/`store_false`. Причина: configargparse превращает строку YAML `flag: false` в `--flag false`, и `store_true` молча проигнорировал бы значение.

`mace/tools/arg_parser_tools.py`:
```python
def check_args(args):
    log_messages = []
    if args.model_dir is None:
        args.model_dir = args.work_dir
    if args.checkpoints_dir is None:
        args.checkpoints_dir = os.path.join(args.work_dir, "checkpoints")
    ...  # проверки согласованности, предупреждения кладутся в log_messages
    return args, log_messages
```

`mace/cli/run_train.py`:
```python
def main() -> None:
    parser = tools.build_default_arg_parser()
    args = parser.parse_args()
    run(args)

def run(args) -> None:
    args, input_log_messages = tools.check_args(args)
    ...  # дальше args передаётся явно: get_loss_fn(args, ...), configure_model(args, ...)
```

## Что сделать у нас

### Новые файлы
- `syscall_hids/tools/arg_parser.py`: `build_default_arg_parser()` и `str2bool()` по образцу выше. Аргументы сгруппировать через `parser.add_argument_group(...)`: Данные, Признаки, Модель, Окна, Обучение, Скоринг и порог, Оценка, Директории, RAM.
- `syscall_hids/tools/arg_parser_tools.py`: `check_args(args) -> (args, log_messages)`.
- `configs/php_cwe_434.yaml`: бывший корневой `config.yaml` (через `git mv`), ключи переименованы под аргументы, к каждому короткий комментарий.
- `configs/flask.yaml`: параметры, с которыми обучена `models/FLASK.pt` (берутся из `hparams` чекпоинта; `dataset_root` указывает на FLASK-датасет, когда он будет).
- `tests/test_arg_parser.py`:
  - без `--config` значения совпадают с таблицей;
  - YAML переопределяет значение по умолчанию;
  - CLI переопределяет YAML;
  - `use_arg_count_feature: false` из YAML даёт `False`;
  - неизвестный ключ в YAML для `hids-train` даёт ошибку (опечатка в конфиге не должна молча игнорироваться).

### Зависимости
В `pyproject.toml` добавить `configargparse` и `pyyaml` как обычные зависимости. В отличие от mace, фолбэка на голый argparse при отсутствии configargparse НЕ делать.

### Правила имён
- snake_case, как в mace: флаг `--batch_size`, ключ YAML `batch_size`.
- Где у mace есть прямой аналог, берём его имя: `lr`, `max_num_epochs`, `restart_latest`, `work_dir`, `model_dir`.

### Таблица параметров

Значения по умолчанию НЕ берутся из этого документа: они равны значениям в `config.yaml` на коммите cdf9d5b. Если в `config.yaml` есть ключ, которого нет в таблице, он тоже становится аргументом с тем же правилом имени. Список таких ключей покажи в плане.

| Было | Аргумент | Примечание |
|---|---|---|
| dataset_root | `--dataset_root` | |
| services | `--services` | `nargs="+"`; заменяет старый `--service` в `run_train` |
| use_arg_count_feature | `--use_arg_count_feature` | str2bool |
| arg_count_buckets | `--arg_count_buckets` | |
| force_rebuild_vocab | `--force_rebuild_vocab` | str2bool |
| embed_dim_syscall / _process / _direction / _arg_count | `--embed_dim_syscall` и т.д. | |
| hidden_dim | `--hidden_dim` | |
| num_layers | `--num_layers` | |
| dropout | `--dropout` | |
| seq_len | `--seq_len` | |
| seq_step | `--seq_step` | |
| batch_size | `--batch_size` | |
| learning_rate | `--lr` | имя как в mace |
| epochs | `--max_num_epochs` | имя как в mace |
| resume | `--restart_latest` | str2bool, имя как в mace |
| window_agg | `--window_agg` | `choices=["quantile", "max", "mean"]` |
| window_agg_quantile | `--window_agg_quantile` | |
| threshold_percentile | `--threshold_percentile` | |
| eval_test_every_epoch | `--eval_test_every_epoch` | str2bool |
| metrics_eval_every_n_epochs | `--metrics_eval_every_n_epochs` | |
| train_metrics_max_batches | `--train_metrics_max_batches` | int или None |
| — | `--work_dir` | новое, по умолчанию `.` |
| model_dir | `--model_dir` | `None` → `{work_dir}/models` |
| — | `--checkpoints_dir` | `None` → `{model_dir}/checkpoints` (чекпоинты эпох), как в mace |
| plots_dir | `--plots_dir` | `None` → `{work_dir}/training_plots` |
| vocab_dir | `--vocab_dir` | `None` → `{work_dir}/vocabs` |
| ram_* | `--ram_guard_enabled`, `--ram_soft_limit_percent`, `--ram_hard_limit_percent`, `--ram_throttle_sleep_sec`, `--ram_check_every_n_recordings` | |

При `work_dir="."` производные пути совпадают с текущими, и поведение не меняется. Если сейчас чекпоинты эпох пишутся не в `{model_dir}/checkpoints`, сохрани текущий путь как вывод по умолчанию и скажи мне.

### Что НЕ становится параметром
Это описание формата данных, а не настройки эксперимента. Сейчас они лежат в `config.py`; они остаются константами в коде:
- `TIME_COLUMN_INDEX`, `PROCESS_NAME_COLUMN_INDEX`, `SYSCALL_COLUMN_INDEX`, `DIRECTION_COLUMN_INDEX`, `PARAMS_BEGIN_INDEX`, `MIN_RAW_FIELDS`, `RECORDING_EXTENSION` → `syscall_hids/data/format.py` (формат строки eBPF-коллектора);
- `TRAIN_SUBDIR`, `VAL_SUBDIR`, `TEST_SUBDIR`, `TEST_NORMAL_SUBDIR`, `TEST_ABNORMAL_SUBDIR` → константы в `syscall_hids/data/layout.py`;
- `ARCHITECTURE_VERSION` остаётся в `modules/models.py`.

### check_args
Только проверки и вывод путей, без изменения смысла параметров:
- вывести `model_dir`, `plots_dir`, `vocab_dir` из `work_dir`, если они `None`;
- `0 < window_agg_quantile <= 1`, `0 < threshold_percentile <= 100`, `0 < seq_step <= seq_len`, `ram_soft_limit_percent < ram_hard_limit_percent`: при нарушении `parser.error`-подобная ошибка;
- если `window_agg == "max"`, а `window_agg_quantile` задан явно, предупредить, что квантиль игнорируется;
- если `use_arg_count_feature` равен False, предупредить, что `embed_dim_arg_count` и `arg_count_buckets` не используются.

### Передача параметров (главная часть работы)
Как в mace: `args` передаётся явно, глобального состояния нет.
- `cli/run_train.py`: `main()` → `build_default_arg_parser().parse_args()` → `run(args)`. `run(args)`: `check_args`, вывести `input_log_messages`, напечатать итоговую конфигурацию, `list_services(args)`, цикл `train_one_service(service, device, args)`.
- `tools/train.py`, `tools/evaluation.py`: принимают `args` и берут значения из него вместо `config.X`.
- `modules/models.py`: `ModelHParams.from_config()` заменить на `ModelHParams.from_args(args)`. `from_checkpoint` не трогать.
- `data/*` (нижний уровень): функции получают конкретные значения явными параметрами (`dataset_root`, `services`, `vocab_dir`, `use_arg_count_feature`, `arg_count_buckets`, `ram_check_every_n_recordings`, `seq_len`, `step`), а не весь `args`. Слой данных не должен зависеть от CLI.
- `tools/resource_guard.py`: проверка RAM вызывается глубоко внутри. Чтобы не тащить параметры через все функции данных, добавить `resource_guard.configure(enabled, soft, hard, sleep_sec)` и вызывать его один раз в `run(args)`. Это единственное разрешённое модульное состояние. Пометь его комментарием.
- `tools/visualization.py`: `plots_dir` передаётся параметром.

### Остальные точки входа
`hids-eval` и `hids-detect` тоже читают конфиг (`MODEL_DIR`, `BATCH_SIZE`, `DATASET_ROOT`). Им нужны свои парсеры с поддержкой `--config` (аналог отдельного парсера `mace_eval_configs`):
- только нужные им параметры: `--config`, `--dataset_root`, `--work_dir`, `--model_dir`, `--batch_size` и их текущие собственные флаги;
- в этих парсерах `ignore_unknown_config_file_keys=True`, чтобы тот же `configs/flask.yaml` подходил и для оценки;
- параметры модели и скоринга (`seq_len`, `window_agg`, порог, словари) берутся из чекпоинта, как сейчас, а не из конфига.

### Воспроизводимость
- Сохранять итоговую конфигурацию (после `check_args`) в чекпоинт отдельным НОВЫМ ключом `"train_args": vars(args)`. Существующие ключи и `from_checkpoint` не трогать.
- Рядом с моделью писать `{model_dir}/{service}_config.yaml` с итоговыми значениями. Его можно сразу передать обратно в `--config` и повторить запуск.

## Чего не делать
- Не менять смысл и значения параметров, логику обучения, скоринга и калибровки.
- Не добавлять новые гиперпараметры, кроме `work_dir`. Seed, logging и прочее — потом и отдельно.
- Не трогать `experiments/` и `flask_app/` (кроме импортов, если они читали `config`).

## Порядок работы
1. План в Plan mode: список функций, у которых меняется сигнатура (было → стало), и откуда каждая получает значения.
2. После моего подтверждения реализовать.
3. Проверка:
   - `pytest tests/` (регрессия и arg_parser) зелёный;
   - `hids-train --help` показывает группы и значения по умолчанию;
   - `grep -rn "import config\|config\.[A-Z]" syscall_hids/` не находит ничего.
4. Обновить в CLAUDE.md разделы «Структура» и «Команды», добавить пример запуска с `--config` и переопределением.
5. Отчёт: что изменено, какие сигнатуры поменялись, что не тронуто.
