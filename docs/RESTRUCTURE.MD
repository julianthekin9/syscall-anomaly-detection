# План реструктуризации в пакет `syscall_hids` (по образцу mace-torch)

Этот документ — задание для Claude Code. Выполняется строго по этапам; каждый этап — отдельная сессия и отдельный коммит. Следующий этап начинается только после того, как я подтвердил предыдущий.

## Главное правило

Это ПЕРЕЕЗД кода, а не переписывание. Тела функций и классов переносятся без изменений логики. Меняются только: расположение, импорты, имена модулей. Любое изменение поведения (скоринг, метрики, формат чекпоинта, гиперпараметры) запрещено, пока я явно не попрошу. Если перенос без изменения логики невозможен, остановись и спроси.

## Целевая структура

```
syscall-anomaly-detection/
├── pyproject.toml                  # пакет + entry points hids-train / hids-eval / hids-detect
├── CLAUDE.md
├── README.md
├── configs/
│   └── flask.yaml                  # (этап 3) параметры запуска вместо правки config.py
├── syscall_hids/                   # устанавливаемый пакет: pip install -e .
│   ├── __init__.py                 # __version__
│   ├── config.py                   # бывший config.py (значения по умолчанию)
│   ├── modules/                    # как mace/modules — только нейросеть
│   │   ├── __init__.py
│   │   ├── models.py               # ARCHITECTURE_VERSION, ModelHParams, CheckpointArchitectureMismatch, SyscallLSTM
│   │   └── scoring.py              # compute_step_scores, aggregate_window_scores, compute_window_scores
│   ├── data/                       # как mace/data — всё про данные
│   │   ├── __init__.py
│   │   ├── parsing.py              # ParsedLine, parse_log_line, read_recording
│   │   ├── layout.py               # _SPLIT_SUBDIR, _root_is_single_service, list_services, _split_dir, recording_files, test_recording_files
│   │   ├── vocab.py                # PAD, UNK, FEATURE_NAMES, vocab_path, save_vocab, load_vocab, _SEQ_DTYPE, _check_vocab_fits_dtype, build_vocab
│   │   ├── sequences.py            # encode_line, num_features, encode_recording, make_sequences, build_normal_sequences, build_test_sequences
│   │   └── datasets.py             # SequenceDataset, TestSequenceDataset (бывший dataset.py)
│   ├── tools/                      # как mace/tools — обучение, оценка, утилиты
│   │   ├── __init__.py
│   │   ├── evaluation.py           # _update_confusion, _macro_precision_from_confusion, evaluate_metrics, calibrate_threshold, quick_test_evaluation, calibrate_and_evaluate
│   │   ├── train.py                # train_one_service, load_resume_checkpoint
│   │   ├── checkpoint.py           # load_model (из predict.py)
│   │   ├── resource_guard.py       # бывший resource_guard.py
│   │   └── visualization.py        # бывший visualization.py
│   ├── collectors/                 # источник событий (eBPF), опциональная зависимость
│   │   ├── __init__.py
│   │   ├── ebpf.py                 # бывший utils/ebpf.py
│   │   └── sudo.py                 # бывший utils/sudo.py
│   ├── detectors/                  # (этап 4) аналог mace/calculators
│   │   ├── __init__.py
│   │   └── detector.py             # AnomalyDetector
│   └── cli/                        # как mace/cli — тонкие точки входа
│       ├── __init__.py
│       ├── run_train.py            # main() из train.py      -> hids-train
│       ├── eval_recordings.py      # main() + score_log_file + print_log_verdict из predict.py -> hids-eval
│       └── detect_live.py          # realtime_detect.py целиком -> hids-detect
├── flask_app/                      # тестовый стенд: НЕ часть пакета
│   └── ...                         # app.py, Dockerfile, сценарии трафика, collect_*.py
├── experiments/                    # НЕ часть пакета, пакет отсюда ничего не импортирует
│   └── lid_ds/
│       ├── convert.py              # LID-DS 2021 -> нативный формат (только stdlib)
│       └── README.md
├── tests/
│   └── test_regression.py          # (этап 2) сверка результатов до/после
└── outputs/                        # в .gitignore: models/, vocabs/, plots/, realtime_runs/
```

## Почему так (кратко)

- `modules/` знает только про тензоры и не импортирует `data/`, кроме `FEATURE_NAMES`.
- `data/` не знает про модель.
- `tools/` склеивает данные и модель.
- `cli/` содержит только разбор аргументов и вызов функций из `tools/`. Логики в `cli/` нет.
- Сейчас `predict.py` импортирует `quick_test_evaluation` из `train.py`, а `realtime_detect.py` импортирует `load_model` из `predict.py`. После переезда оба импорта идут из `tools/`, и точки входа перестают зависеть друг от друга.
- `experiments/lid_ds/` — внешний источник данных. Он приводит LID-DS к нативному формату и раскладке, а дальше данные идут через общий интерфейс. В `syscall_hids/` не должно быть кода, знающего про LID-DS (zip, json, 8 колонок, время эксплойта), и `experiments/` не импортирует `syscall_hids`.
- Стенд `flask_app/` нужен для сбора данных и в пакет не входит. Он импортирует коллектор как `from syscall_hids.collectors.ebpf import EbpfSession`.

## Этапы

### Этап 1. Пакет и перенос файлов (без изменения логики)
1. Создать `pyproject.toml` (setuptools, `packages = find: include syscall_hids*`), зависимости только прямые: torch, numpy, scikit-learn, matplotlib, psutil. Extra `[testbed]`: flask, requests. BCC в зависимости не добавлять: он ставится системно (`apt install python3-bpfcc`), упомянуть это в README.
2. Перенести код по таблице выше через `git mv` там, где файл переезжает целиком, чтобы сохранилась история.
3. Заменить импорты на абсолютные: `from syscall_hids.data.sequences import make_sequences` и т.п. Модули, читающие `config`, импортируют `from syscall_hids import config`.
4. Пути в `config.py` (`DATASET_ROOT`, `VOCAB_DIR`, `MODEL_DIR`, `PLOTS_DIR`) пока не менять.
5. Entry points в `pyproject.toml`:
   - `hids-train = syscall_hids.cli.run_train:main`
   - `hids-eval = syscall_hids.cli.eval_recordings:main`
   - `hids-detect = syscall_hids.cli.detect_live:main`
6. Удалить из git закоммиченные `__pycache__/`, png и csv с результатами (`git rm --cached`), дополнить `.gitignore`.
7. Проверка: `pip install -e .`, `python -c "import syscall_hids.cli.run_train, syscall_hids.cli.eval_recordings"`, `hids-train --help` (если есть argparse). Модули с `bcc` проверять импортом только если bcc установлен.
8. В конце перечислить: какие файлы перенесены куда, какие импорты изменены, что не тронуто.

### Этап 2. Регрессионный тест
`tests/test_regression.py`: на маленьком фиксированном наборе записей загрузить существующий чекпоинт и сравнить оконные скоры и AUC со значениями, сохранёнными ДО переезда (сохранить их скриптом из старого кода в `tests/golden/`). Совпадение до 1e-6. Пока тест не зелёный, дальше не идём.

### Этап 3. Конфиг через аргументы и YAML (как `--config` в mace)
`syscall_hids/tools/arg_parser.py`: argparse + загрузка YAML; значения по умолчанию берутся из `config.py`. Обсудить со мной ДО реализации, как передавать конфиг: явно аргументом в функции или через переопределение модуля `config`.

### Этап 4. AnomalyDetector (аналог MACECalculator)
`AnomalyDetector.load(path)` читает чекпоинт (в нём уже есть vocabs, hparams, seq_len, window_agg, порог); `score_rows(rows) -> float`; `is_anomaly(score) -> bool`. `detect_live.py` переводится на детектор, `encode_tail` переносится в детектор. Только после моего подтверждения.

## Чего не делать
- Не менять тела функций, сигнатуры, значения констант и формат чекпоинта.
- Не трогать `flask_app/app.py`, Dockerfile и docker-compose.
- Не трогать `experiments/` при переезде пакета.
- Не запускать `sudo`, eBPF-сбор и полное обучение. Если нужен прогон, дать мне команду.
- Не объединять этапы.