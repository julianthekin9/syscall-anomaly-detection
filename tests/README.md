# Тесты

```
pip install -e .[dev]
pytest tests/ -v
```

| Тест | Что проверяет |
|---|---|
| `test_regression.py` | Инференс: оконные скоры и AUC на фикстурах совпадают с эталоном (допуск 1e-6). Два чекпоинта: `FLASK.pt` (реальный старый чекпоинт; его словарь почти не покрывает фикстуры, процесс всегда UNK) и `FIXT.pt` (словарь построен на тех же данных) |
| `test_train_regression.py` | Мини-обучение `train_one_service` на датасете FIXT: словари, `vocab_sizes`, `hparams` точно; порог, loss/precision по эпохам, AUC на test по эпохам, `(sum, norm)` каждого тензора `state_dict` с допуском 1e-5 |
| `test_cli_eval.py` | `hids-eval --eval-test-split` на фикстурах отрабатывает, AUC равен эталонному |

## Эталон

Эталон снят со старого кода, до переезда в пакет: коммит `3c9ffac`, ветка `DATASET_FORMAT="generic"`. Все значения лежат в `tests/golden/golden.json`:
- `auc`, `scores` — инференс `FLASK.pt`;
- `fixt_inference` — инференс `FIXT.pt`;
- `train` — мини-обучение, вместе с параметрами `config` и seed, с которыми оно запускалось.

Данные:
- `tests/golden/data/{normal,abnormal}` — по 3 записи из test-сплита `DATASET_LIDDS/PHP_CWE-434`, первые 1000 строк;
- `tests/golden/data/FIXT/` — мини-датасет: 3 записи train и 2 записи validation (первые 1000 строк), test — копия фикстур выше.

Эталон не перегенерируется при изменениях кода пакета: смысл теста в сравнении со старым кодом. На этапе 3 `test_train_regression.py` переписывается под `args`, а `golden.json` и `FIXT.pt` остаются прежними.

Перегенерация, только если меняется сам набор фикстур:

```
python tests/golden/make_golden.py --make-fixtures DATASET_LIDDS/PHP_CWE-434/test
python tests/golden/make_golden.py --make-fixt DATASET_LIDDS/PHP_CWE-434

git worktree add ../old 3c9ffac
python tests/golden/make_golden.py --old-code ../old           # инференс FLASK.pt
python tests/golden/make_golden.py --old-code ../old --train   # мини-обучение, FIXT.pt, инференс FIXT.pt
git worktree remove --force ../old
```

## Допуски

Допуски 1e-6 (инференс) и 1e-5 (обучение) рассчитаны на CPU и ту же версию torch, с которой снят эталон (torch 2.14.1+cpu). Обучение детерминировано: seed 0 для `random`, `numpy` и `torch`, `torch.use_deterministic_algorithms(True)`. На GPU или другой версии torch числа могут разойтись сильнее допуска, и это не будет ошибкой кода.
