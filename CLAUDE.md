# HIDS: LSTM-детектор аномалий системных вызовов Linux

Дипломный проект. Host-based IDS: LSTM обучается только на нормальном поведении и предсказывает следующий syscall; аномалия = высокий NLL. Мониторится Flask-приложение в Docker, живой сбор трасс через eBPF/BCC. Основной датасет: LID-DS 2021 (сценарии Apache Tomcat CVE).

## Язык
- Отвечай мне на русском.
- Комментарии в коде и docstring пиши на украинском.
- Тексты для диплома: сжатая, фактическая научная украинская проза без markdown-разметки (текст потом переформатируется другим инструментом). В блок-схемах только описательный текст, без имён переменных и ссылок на код.

## Структура
Идёт переезд в пакет `syscall_hids` по образцу mace-torch. План, целевая структура и этапы: `docs/RESTRUCTURE.md`. Работая над реструктуризацией, сначала прочитай этот файл и делай только текущий этап.

Текущая (старая) раскладка:
- `config.py`: гиперпараметры, пути, индексы колонок трассы. Читается как глобальный модуль (`import config`).
- `data.py`: парсинг трасс (`ParsedLine`), словари, `make_sequences`, `build_normal_sequences` / `build_test_sequences`.
- `dataset.py`: `SequenceDataset`, `TestSequenceDataset`.
- `model.py`: `SyscallLSTM`, `ModelHParams`, `ARCHITECTURE_VERSION`, функции скоринга.
- `train.py`: обучение, метрики, калибровка порога, `quick_test_evaluation`.
- `predict.py`: оффлайн-инференс, `load_model`.
- `realtime_detect.py`: живая детекция поверх eBPF.
- `visualization.py`, `resource_guard.py`.
- `utils/ebpf.py`: eBPF-сбор (`EbpfSession`, `Collector`, `RealTimeCollector`); `utils/sudo.py`.
- `flask_app/`: тестовый стенд (Flask-приложение, Docker, сценарии трафика, сбор датасета).
- `experiments/lid_ds/convert.py`: самостоятельный конвертер LID-DS 2021 в нативный формат (stdlib, без импорта проекта). Логику, специфичную для LID-DS, держать только там. Подробности в `experiments/lid_ds/README.md`.

## Текущая архитектура (стабильна, не менять без явной просьбы)
- Одна выходная голова: предсказание следующего syscall. Голова предсказания процесса удалена навсегда (AUC идентичен до 4 знака); `USE_PROCESS_HEAD` не возвращать.
- Входные эмбеддинги: syscall, process, direction, arg_count (16 + 8 + 2 + 4 = 30).
- HIDDEN_DIM=128, NUM_LAYERS=2, SEQ_LEN=64, SEQ_STEP=32.
- Скоринг: NLL на шаг, агрегация окна через `WINDOW_AGG="quantile"` (0.90). Top-k удалён.
- Порог: `THRESHOLD_PERCENTILE=99.0` на validation split.
- Чекпоинт: `ModelHParams.from_checkpoint` делает прямой `cls(**checkpoint["hparams"])` без fallback и shim'ов обратной совместимости.

## Инварианты и известные нюансы
- `ARCHITECTURE_VERSION` живёт в `model.py`, это маркер структуры `state_dict`, а не гиперпараметр. Инкрементировать только при изменении структуры `state_dict`.
- `encode_tail()` в `realtime_detect.py` локальный намеренно. Переносить его только на этапе 4 плана (AnomalyDetector).
- Разметка ground truth на уровне окна/времени, не всего файла: whole-file labeling уже однажды обрушил AUC до ~0.66.
- Высокий NLL в realtime после остановки трафика: это idle/keepalive паттерны, отсутствующие в train, а не баг.
- Память: последовательности только numpy `int16`, тестовая оценка потоковая по записям. Не возвращать списки Python int и не грузить весь test в память.
- Изменение формата eBPF-события (`event_t` / `Event` / `Collector`) требует синхронного обновления индексов колонок в `config.py`.

## Как работать с кодом
- Минимальный scope: меняй только то, о чём я прямо попросил. Не трогай соседние файлы и не делай попутный рефакторинг. Если считаешь, что нужно больше, сначала спроси.
- Новую функциональность, которая усложнила бы ядро, выноси в отдельный самостоятельный скрипт.
- Мёртвый код удаляй (неиспользуемые импорты, константы, fallback-ветки), а не прячь за флагами.
- После правок кратко перечисли: что изменено (файл, функция) и что намеренно не тронуто.
- eBPF-код требует root. Не запускай `sudo`, eBPF-сбор и `flask_app/collect_*.py` сам: дай мне команду, я запущу.
- Не читай целиком сырые трассы LID-DS: они огромные. Если нужен формат, смотри `head` одного файла.

## Команды
<!-- заполни под себя -->
- Конвертация LID-DS: `python experiments/lid_ds/convert.py <LID_DS_ROOT> ./DATASET_LIDDS --pre-attack-to-normal`
- Обучение: `python train.py`
- Оффлайн-оценка: `python predict.py`
- Realtime (root): `sudo python realtime_detect.py`