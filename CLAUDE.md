# HIDS: LSTM-детектор аномалий системных вызовов Linux

Дипломный проект. Host-based IDS: LSTM обучается только на нормальном поведении и предсказывает следующий syscall; аномалия = высокий NLL. Мониторится Flask-приложение в Docker, живой сбор трасс через eBPF/BCC. Основной датасет: LID-DS 2021 (сценарии Apache Tomcat CVE).

## Язык
- Отвечай мне на русском.
- Комментарии в коде и docstring пиши на украинском.
- Тексты для диплома: сжатая, фактическая научная украинская проза без markdown-разметки (текст потом переформатируется другим инструментом). В блок-схемах только описательный текст, без имён переменных и ссылок на код.

## Структура
Идёт переезд в пакет `syscall_hids` по образцу mace-torch. План, целевая структура и этапы: `docs/RESTRUCTURE.md`. Работая над реструктуризацией, сначала прочитай этот файл и делай только текущий этап.

Раскладка (после этапов 1–2):
- `syscall_hids/config.yaml`: основной конфиг эксперимента (данные, признаки, модель, окна, обучение, скоринг, пути, RAM). Единственное место для тюнинга. Все ключи обязательны, неизвестный ключ даёт ошибку при импорте.
- `syscall_hids/config.py`: читает `config.yaml` в атрибуты модуля (`from syscall_hids import config`, `config.SEQ_LEN`) и хранит константы формата трасс (индексы колонок, имена подпапок, расширение).
- `syscall_hids/data/`: `parsing.py` (`ParsedLine`, `read_recording`), `layout.py` (раскладка сплитов, `list_services`), `vocab.py` (словари), `sequences.py` (`encode_*`, `make_sequences`, `build_normal_sequences` / `build_test_sequences`), `datasets.py` (`SequenceDataset`, `TestSequenceDataset`).
- `syscall_hids/modules/`: `models.py` (`SyscallLSTM`, `ModelHParams`, `ARCHITECTURE_VERSION`), `scoring.py` (NLL на шаг, агрегация окна).
- `syscall_hids/tools/`: `train.py` (`train_one_service`, чекпоинты), `evaluation.py` (метрики, калибровка порога, `quick_test_evaluation`), `checkpoint.py` (`load_model`), `visualization.py`, `resource_guard.py`.
- `syscall_hids/collectors/`: `ebpf.py` (`EbpfSession`, `Collector`, `RealTimeCollector`), `sudo.py`.
- `syscall_hids/cli/`: точки входа `run_train.py` (`hids-train`), `eval_recordings.py` (`hids-eval`), `detect_live.py` (`hids-detect`, живая детекция поверх eBPF).
- `tests/`: `test_regression.py` сверяет оконные скоры и AUC с эталоном из кода до переезда (`tests/golden/`).
- `flask_app/`: тестовый стенд (Flask-приложение, Docker, сценарии трафика, сбор датасета).
- `experiments/lid_ds/convert.py`: самостоятельный конвертер LID-DS 2021 в нативный формат (stdlib, без импорта проекта). Логику, специфичную для LID-DS, держать только там. Подробности в `experiments/lid_ds/README.MD`.

## Текущая архитектура (стабильна, не менять без явной просьбы)
- Одна выходная голова: предсказание следующего syscall. Голова предсказания процесса удалена навсегда (AUC идентичен до 4 знака); `USE_PROCESS_HEAD` не возвращать.
- Конкретные значения гиперпараметров здесь не записываются: они только в `syscall_hids/config.yaml` (размерности, число слоёв, длина и шаг окна, агрегация, перцентиль порога).
- Входные эмбеддинги: четыре признака (syscall, process, direction, arg_count), конкатенируются и идут в многослойный LSTM.
- Скоринг: NLL настоящего следующего syscall на каждом шаге, затем агрегация шагов в оценку окна (`window_agg`). Top-k удалён.
- Порог: перцентиль оконных оценок на validation split.
- Чекпоинт: `ModelHParams.from_checkpoint` делает прямой `cls(**checkpoint["hparams"])` без fallback и shim'ов обратной совместимости.

## Инварианты и известные нюансы
- `ARCHITECTURE_VERSION` живёт в `syscall_hids/modules/models.py`, это маркер структуры `state_dict`, а не гиперпараметр. Инкрементировать только при изменении структуры `state_dict`.
- `encode_tail()` в `syscall_hids/cli/detect_live.py` локальный намеренно. Переносить его только на этапе 4 плана (AnomalyDetector).
- Разметка ground truth на уровне окна/времени, не всего файла: whole-file labeling уже однажды обрушил AUC до ~0.66.
- Высокий NLL в realtime после остановки трафика: это idle/keepalive паттерны, отсутствующие в train, а не баг.
- Память: последовательности только numpy `int16`, тестовая оценка потоковая по записям. Не возвращать списки Python int и не грузить весь test в память.
- Изменение формата eBPF-события (`event_t` / `Event` / `Collector`) требует синхронного обновления индексов колонок в `syscall_hids/config.py`.

## Как работать с кодом
- Минимальный scope: меняй только то, о чём я прямо попросил. Не трогай соседние файлы и не делай попутный рефакторинг. Если считаешь, что нужно больше, сначала спроси.
- Новую функциональность, которая усложнила бы ядро, выноси в отдельный самостоятельный скрипт.
- Мёртвый код удаляй (неиспользуемые импорты, константы, fallback-ветки), а не прячь за флагами.
- После правок кратко перечисли: что изменено (файл, функция) и что намеренно не тронуто.
- eBPF-код требует root. Не запускай `sudo`, eBPF-сбор и `flask_app/collect_*.py` сам: дай мне команду, я запущу.
- Не читай целиком сырые трассы LID-DS: они огромные. Если нужен формат, смотри `head` одного файла.

## Команды
<!-- заполни под себя -->
- Установка: `pip install -e .[dev]`
- Конвертация LID-DS: `python experiments/lid_ds/convert.py LID-DS_DATASET/<сценарий>.zip --out ./DATASET_LIDDS --balance-test`
- Параметры запуска: правка `syscall_hids/config.yaml`
- Обучение: `hids-train` (или `hids-train --service <сценарий>`)
- Оффлайн-оценка: `hids-eval --service <сценарий> --log <файл.sc>`
- Realtime (root): `sudo hids-detect --service <сценарий> --container flask-app`
- Тесты: `pytest tests/`