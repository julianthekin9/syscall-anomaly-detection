# Этап 2б. Исправления и расширение регрессии (перед этапом 3)

Задание для Claude Code. Каждый пункт части A — отдельный маленький коммит. Часть B — один коммит. Этап 3 начинается только после того, как всё это готово и `pytest tests/` зелёный.

## Часть A. Исправления известных проблем

Порядок: A1 → A6. В каждом коммите только то, что относится к пункту.

**A1. `hids-eval --eval-test-split` падает с TypeError.** `quick_test_evaluation` вызывается без `service_name`. Передать сервис из `--service`. Ошибка была и в старом `predict.py`, поэтому это исправление, а не изменение поведения. Добавить `tests/test_cli_eval.py`: `hids-eval --eval-test-split` на фикстурах из `tests/golden/` отрабатывает без исключения, а AUC совпадает с эталонным из `golden.json`.

**A2. `hids-detect --checkpoint` падает.** Внутри функции остался импорт `from model import SyscallLSTM`. Заменить на импорт из пакета. Затем найти ВСЕ оставшиеся старые импорты в любом месте строки, не только в начале:
```
grep -rnE "(^|\s)(import|from) (config|data|dataset|model|train|predict|visualization|resource_guard|utils)(\s|\.|$)" syscall_hids/ flask_app/ tests/
```
Плюс `python -m pyflakes syscall_hids/`. Исправить всё найденное.

**A3. `hids-detect`: зашитые `CONTAINER` и `SERVICE`.** Добавить флаги `--service` (по умолчанию `FLASK`) и `--container` (по умолчанию `flask-app`), которые обещает docstring. Значения по умолчанию равны нынешним константам, так что поведение без флагов не меняется.

**A4. ROC-кривая пишется в текущую папку и перезаписывается на каждой эпохе.** Писать в `config.PLOTS_DIR` как `{service}_roc_epoch{N:03d}.png` и отдельно `{service}_roc_final.png` для итоговой модели. Числа не меняются, меняется только путь к файлу.

**A5. Конфиг указывает на сырой LID-DS.** В `config.yaml`: `dataset_root: ./DATASET_LIDDS`, `services: [PHP_CWE-434]`. Это решение по данным, его коммит отдельный.

**A6. Чистка.** Каждое действие сначала покажи списком, ничего не удаляй молча.
- удалить `requirements.txt` (зависимости живут в `pyproject.toml`), пустую `utils/`, корневой `__pycache__/`;
- `git rm unpack_lid_ds.py` (устарел);
- `split_dataset.py`: если он про LID-DS, перенести (`git mv`) в `experiments/lid_ds/`, если про стенд, то в `flask_app/`. Сначала скажи мне, что он делает;
- `plot_log_figures.py` пока оставить: на этапе 3б его заменит `hids-plot-train`;
- в `.claude/settings.json` добавить deny на чтение больших сырых трасс: `"Read(./normal_training.sc)"`, `"Read(./ApachePHP_normal.sc)"`, `"Read(./LID-DS_DATASET/**)"`, `"Read(./DATASET*/**)"`;
- в `load_model` исправить подсказку `python train.py` на `hids-train`;
- в CLAUDE.md убрать конкретные значения гиперпараметров из раздела «Текущая архитектура». Оставить только структурные факты (одна голова, 4 эмбеддинга, LSTM, NLL, агрегация окна, порог по перцентилю на validation) и сослаться на конфиг для значений. Иначе значения в CLAUDE.md снова разойдутся с YAML.

## Часть B. Эталон мини-обучения

Сейчас регрессия покрывает только инференс (96 окон на 6 фикстурах с чекпоинтом FLASK). Этап 3 переписывает в основном обучение: построение словаря, `ModelHParams`, `seq_step`, `lr`, калибровку порога, чекпоинт. Без эталона обучения ошибка там пройдёт незамеченной.

1. **Мини-датасет из уже лежащих фикстур:** `tests/golden/data/FIXT/{training,validation,test/normal,test/abnormal}`. В training и validation — нормальные файлы, не пересекающиеся с test. Если нормальных фикстур не хватает, добавь ещё по 2–3 файла (первые 1000 строк) из `DATASET_LIDDS/PHP_CWE-434/{training,validation}`.

2. **`tests/golden/make_golden.py --train`** запускается против СТАРОГО кода (worktree `3c9ffac`, как для текущего эталона):
   - `torch.manual_seed(0)`, `numpy.random.seed(0)`, `random.seed(0)`, `torch.use_deterministic_algorithms(True)`, CPU, `num_workers=0`;
   - явно переопределить модуль `config` и не полагаться на умолчания: `DATASET_ROOT` = мини-датасет, `SERVICES=["FIXT"]`, `EPOCHS=2`, `HIDDEN_DIM=32`, `NUM_LAYERS=2`, `SEQ_LEN=64`, `SEQ_STEP=32`, `BATCH_SIZE=16`, `LEARNING_RATE=1e-3`, `MODEL_DIR` / `PLOTS_DIR` / `VOCAB_DIR` во временной папке, `FORCE_REBUILD_VOCAB=True`, `RESUME=False`, `EVAL_TEST_EVERY_EPOCH=True`. Если в старом коде было `DATASET_FORMAT`, поставить нативный формат;
   - вызвать `train_one_service("FIXT", cpu)`;
   - сохранить в `golden.json` → `train`: словари, `vocab_sizes`, `hparams`, `threshold`, итоговые метрики на test, train loss по эпохам и для каждого тензора `state_dict` пару `(sum, norm)`;
   - итоговый чекпоинт положить в `tests/golden/FIXT.pt`.

3. **`tests/test_train_regression.py`** вызывает новый `train_one_service` с теми же значениями и тем же seed. Сравнивает всё из п.2: допуск 1e-5 для float, точное совпадение для словарей и hparams. В docstring записать: «на этапе 3 этот тест переписывается под `args`, эталон (`golden.json`, `FIXT.pt`) НЕ перегенерируется».

4. **Перед генерацией** сообщи долю UNK на фикстурах со словарём FLASK.pt. Если она больше 50%, инференс-тест на FLASK.pt почти ничего не проверяет в кодировании. Тогда добавь второй инференс-тест на `FIXT.pt` (его словарь совпадает с фикстурами), а тест на FLASK.pt оставь как проверку «реальный старый чекпоинт загружается и даёт те же скоры».

5. **Санити:** временно поменяй в новом тесте `SEQ_STEP` на 16 и убедись, что тест падает. Верни.

6. В `tests/README.md` записать:
   - хеш коммита, с которого снят эталон;
   - команды перегенерации;
   - что допуски рассчитаны на CPU и ту же версию torch.

## Проверка
- `pytest tests/ -v` зелёный: регрессия инференса, регрессия обучения, eval CLI;
- `git status` чистый, worktree удалён;
- отчёт: список коммитов и что в каждом.
