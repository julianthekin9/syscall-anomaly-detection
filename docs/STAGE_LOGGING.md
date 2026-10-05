# Этап 3б. Логирование обучения как в mace-torch

Задание для Claude Code. Выполняется после этапа 3: нужны `args`, `check_args` и `--work_dir`. Предусловие: `pytest tests/` зелёный.

## Цель

1. Все `print()` на пути обучения заменяются на стандартный `logging`. Лог пишется одновременно в консоль и в файлы.
2. Метрики каждого шага и каждой эпохи пишутся в машиночитаемый JSONL-файл (как `MetricsLogger` в mace). По нему можно построить графики и сравнить запуски, даже если процесс упал или Colab отключился.
3. В начале лога записываются версия пакета, git-коммит и полная итоговая конфигурация. Любой запуск должен быть воспроизводим по своему логу.

## Как это сделано в mace-torch (образец)

`mace/tools/utils.py`:
```python
def get_tag(name: str, seed: int) -> str:
    return f"{name}_run-{seed}"

def setup_logger(level=logging.INFO, tag=None, directory=None, rank=0):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    ch = logging.StreamHandler(stream=sys.stdout)       # консоль: уровень level
    ch.setLevel(level); ch.setFormatter(formatter); logger.addHandler(ch)
    if directory is not None and tag is not None:
        os.makedirs(directory, exist_ok=True)
        fh_main = logging.FileHandler(os.path.join(directory, f"{tag}.log"))         # уровень level
        fh_main.setLevel(level); fh_main.setFormatter(formatter); logger.addHandler(fh_main)
        fh_debug = logging.FileHandler(os.path.join(directory, f"{tag}_debug.log"))  # всё, включая DEBUG
        fh_debug.setLevel(logging.DEBUG); fh_debug.setFormatter(formatter); logger.addHandler(fh_debug)

class UniversalEncoder(json.JSONEncoder):           # numpy/torch -> JSON
    def default(self, o):
        if isinstance(o, np.integer): return int(o)
        if isinstance(o, np.floating): return float(o)
        if isinstance(o, np.ndarray): return o.tolist()
        if isinstance(o, torch.Tensor): return o.detach().cpu().numpy().tolist()
        return json.JSONEncoder.default(self, o)

class MetricsLogger:                                # JSONL: одна строка = один словарь
    def __init__(self, directory: str, tag: str) -> None:
        self.directory = directory
        self.path = os.path.join(directory, tag + ".txt")
    def log(self, d: dict) -> None:
        os.makedirs(self.directory, exist_ok=True)
        with open(self.path, mode="a", encoding="utf-8") as f:
            f.write(json.dumps(d, cls=UniversalEncoder)); f.write("\n")
```

`mace/cli/run_train.py`, начало `run(args)`:
```python
tag = tools.get_tag(name=args.name, seed=args.seed)
args, input_log_messages = tools.check_args(args)
tools.set_seeds(args.seed)
tools.setup_logger(level=args.log_level, tag=tag, directory=args.log_dir)
logging.info("===========VERIFYING SETTINGS===========")
for message, loglevel in input_log_messages:
    logging.log(level=loglevel, msg=message)
logging.info(f"MACE version: {mace.__version__}")
logging.debug(f"Configuration: {args}")
commit = print_git_commit()                         # logging.debug(f"Current Git commit: {commit}")
...
logger = tools.MetricsLogger(directory=args.results_dir, tag=tag + "_train")
```

`mace/tools/train.py`:
- каждый шаг оптимизации: `opt_metrics["mode"] = "opt"; opt_metrics["epoch"] = epoch; logger.log(opt_metrics)`;
- каждая валидация: `eval_metrics["mode"] = "eval"; eval_metrics["epoch"] = epoch; logger.log(eval_metrics)` и одна строка в лог: `Epoch {epoch}: head: ..., loss=..., <метрики>`.

Лог разбит на секции заголовками: `===========VERIFYING SETTINGS===========`, `LOADING INPUT DATA`, `MODEL DETAILS`, `OPTIMIZER INFORMATION`, `TRAINING`, `RESULTS`.

## Что сделать у нас

### Новые аргументы (в `tools/arg_parser.py`, группа «Логирование»)
| Аргумент | По умолчанию | Примечание |
|---|---|---|
| `--name` | `hids` | имя эксперимента, входит в tag |
| `--seed` | `123` | как в mace; `set_seeds` вызывается в начале `run` |
| `--log_level` | `INFO` | `choices=["DEBUG","INFO","WARNING","ERROR"]` |
| `--log_dir` | `None` → `{work_dir}/logs` | вывод в `check_args` |
| `--results_dir` | `None` → `{work_dir}/results` | вывод в `check_args` |

`check_args` перестаёт печатать предупреждения и возвращает их в `log_messages` списком `(message, logging.WARNING)`, как в mace.

### Новый модуль `syscall_hids/tools/utils.py`
`get_tag`, `setup_logger`, `UniversalEncoder`, `MetricsLogger`, `set_seeds(seed)` (random, numpy, torch, torch.cuda), `get_git_commit()`. Код по образцу выше. `get_git_commit` вызывает `git rev-parse HEAD` через subprocess; если git нет, возвращает `"None"`. Пакет GitPython не добавлять.

`setup_logger` нужно сделать идемпотентным: перед добавлением своих хендлеров удалять ранее добавленные. Иначе при повторном вызове в Colab/Jupyter каждая строка задвоится.

### Теги и файлы
- Лог запуска: `tag = get_tag(args.name, args.seed)`, то есть `{log_dir}/{name}_run-{seed}.log` и `{log_dir}/{name}_run-{seed}_debug.log`.
- Метрики по сервисам: `MetricsLogger(args.results_dir, f"{name}_{service}_run-{seed}_train")`, то есть `{results_dir}/{name}_{service}_run-{seed}_train.txt`.
- При `--restart_latest true` файлы дописываются, а не перезаписываются, как в mace.

### Начало `run(args)` (порядок как в mace)
`get_tag` → `check_args` → `set_seeds` → `setup_logger` → секция `VERIFYING SETTINGS` (сообщения из `check_args`) → `logging.info` с версией `syscall_hids.__version__` и устройством → `logging.debug(f"Configuration: {vars(args)}")` → `logging.debug` с git-коммитом. Коммит также сохраняется в чекпоинт ключом `"git_commit"`, рядом с `train_args` из этапа 3.

### Секции лога в `train_one_service`
- `===========LOADING INPUT DATA===========`: сервис, размеры словарей, число train/val/test окон, доли атакующих окон в test.
- `===========MODEL DETAILS===========`: `hparams`, `ARCHITECTURE_VERSION`, число обучаемых параметров (`sum(p.numel() for p in model.parameters() if p.requires_grad)`).
- `===========OPTIMIZER INFORMATION===========`: оптимизатор, `lr`, `batch_size`, `max_num_epochs`, число шагов на эпоху.
- `===========TRAINING===========`: одна строка INFO на эпоху: `Epoch {n}/{max}: train_loss=..., val_nll=..., macro_precision=..., time=...s`. Конкретный набор полей бери из того, что код уже считает. Новые метрики не придумывай.
- `===========RESULTS===========`: порог, итоговые метрики на test, путь к сохранённой модели, путь к файлу метрик.

### Что писать в JSONL
Писать только то, что уже вычисляется. Новые вычисления не добавлять.
- `{"mode": "opt", "epoch": e, "step": s, "loss": ..., "lr": ...}` на каждый шаг. Если это заметно замедляет обучение (файл открывается на каждый шаг), добавь `--log_every_n_steps` (по умолчанию 1) и скажи мне.
- `{"mode": "eval", "epoch": e, "split": "val", "loss": ..., <метрики валидации>, "time": ...}` на каждую валидацию.
- `{"mode": "test", "epoch": e, <метрики test: auc, precision, recall, f1 и т.д., что уже считается>}` там, где сейчас считаются diagnostics на test.
- `{"mode": "threshold", "epoch": e, "threshold": ..., "percentile": ..., "window_agg": ..., "window_agg_quantile": ...}` при калибровке порога.
- `{"mode": "ram", "epoch": e, "rss_gb": ..., "ram_percent": ...}` раз в эпоху (из `resource_guard`).

### Замена print
- На пути обучения (`cli/run_train.py`, `tools/train.py`, `tools/evaluation.py`, `data/*`, `tools/resource_guard.py`, `tools/visualization.py`) все `print()` превращаются в `logging.info` / `logging.warning` / `logging.debug`. Текст сообщений не меняется, только уровень.
- Уровни:
  - предупреждения (пропуск сервиса, пустой test, чекпоинт не найден, срабатывание soft-лимита RAM) → WARNING;
  - прогресс по записям и подробности → DEBUG;
  - всё остальное → INFO.
- `classification_report` из sklearn — многострочная таблица, её логировать одним сообщением: `logging.info("\n" + report)`.
- В модулях использовать корневой `logging` (как в mace), а не `logging.getLogger(__name__)`. Тогда все сообщения попадают в одни и те же файлы.
- `hids-eval` и `hids-detect` на этом этапе не трогать: у них интерактивный вывод в консоль, это отдельная задача.

### Графики из файла метрик (как `mace/cli/visualise_train.py`)
`tools/visualization.py` получает функцию `plot_from_results(results_path, out_path)`: читает JSONL и строит те же кривые, что сейчас `plot_training_curves` строит из словаря `history`. Новая команда `hids-plot-train --results <файл> [--out <png>]` (entry point в `pyproject.toml`). Существующий `plot_training_curves` пока оставить как есть. Переводить обучение на новую функцию — только после моего подтверждения.

## Тесты
- `tests/test_logging.py`: мини-обучение на фикстурах из `tests/golden/` во временном `work_dir`, после него:
  - существуют `logs/{tag}.log`, `logs/{tag}_debug.log` и `results/..._train.txt`;
  - каждая строка JSONL парсится через `json.loads`;
  - в файле есть режимы `opt`, `eval` и `threshold`;
  - в `.log` есть секции `VERIFYING SETTINGS` и `RESULTS`;
  - в `_debug.log` есть `Configuration:`.
- `setup_logger`, вызванный дважды, не задваивает строки.
- Регрессионные тесты этапа 2 остаются зелёными без перегенерации эталона. Логирование не должно менять ни одно число.
- `grep -rn "print(" syscall_hids/cli/run_train.py syscall_hids/tools/ syscall_hids/data/` ничего не находит, кроме `hids-plot-train`, если там нужен вывод.

## Чего не делать
- Не менять логику обучения, метрики, порог и формат существующих ключей чекпоинта.
- Не добавлять wandb, tensorboard и прочие внешние зависимости.
- Не переводить и не переписывать тексты сообщений.

## Порядок работы
1. План в Plan mode:
   - список всех `print`, которые станут `logging`, с уровнями;
   - точные места, где пишутся записи `opt` / `eval` / `test` / `threshold`;
   - какие метрики есть в каждой записи.
2. После подтверждения реализовать.
3. `pytest tests/`, затем короткий прогон `hids-train --config configs/flask.yaml --max_num_epochs 1 --work_dir /tmp/run`. Покажи мне первые 40 строк `.log` и 5 строк JSONL.
4. Обновить CLAUDE.md: раздел «Команды» (`hids-plot-train`) и описание того, где лежат логи.
5. Отчёт: что изменено, что не тронуто.
