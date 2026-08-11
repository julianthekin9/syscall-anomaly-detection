"""Обучение per-service LSTM для next-syscall prediction (LID-DS 2021).

    train-сплит (чисто нормальный) -> обучение модели предсказывать
        следующий syscall
    val-сплит (чисто нормальный, held-out) -> калибровка порога тревоги
        (config.THRESHOLD_PERCENTILE-й перцентиль anomaly score)
    test-сплит (норма+атаки) -> быстрая diagnostics-оценка (precision/
        recall/AUC по окнам, используя известную разметку атак только для
        ОЦЕНКИ — модель её никогда не видит при обучении)

Использование:
    python train.py                      # все сервисы из config.LID_DS_ROOT
    python train.py --service CVE-2012-2122
"""

import argparse
import gc
import os

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import classification_report, roc_auc_score
from torch.utils.data import DataLoader

import config
import resource_guard
from data import build_normal_sequences, build_test_sequences, build_vocab, list_services
from dataset import EvalSequenceDataset, SequenceDataset
from model import ARCHITECTURE_VERSION, ModelHParams, SyscallLSTM, aggregate_window_scores, combine_step_scores, compute_step_scores_components
from visualization import plot_training_curves


def _update_confusion(cm: torch.Tensor, y_true: torch.Tensor, y_pred: torch.Tensor, num_classes: int) -> None:
    """cm: [num_classes, num_classes] (строки — истина, столбцы — предсказание),
    аккумулируется по батчам через bincount. Компактно: не хранит сырые
    предсказания/таргеты в памяти (на train с миллионами шагов это были бы
    десятки-сотни МБ на КАЖДУЮ метрическую эпоху) — только саму матрицу
    (для словаря syscall'ов ~30-100 значений это единицы КБ)."""
    idx = y_true.reshape(-1).long() * num_classes + y_pred.reshape(-1).long()
    cm += torch.bincount(idx, minlength=num_classes * num_classes).reshape(num_classes, num_classes)


def _macro_precision_from_confusion(cm: torch.Tensor) -> float:
    """Macro-precision по накопленной confusion matrix: TP_c/(TP_c+FP_c) на
    класс, усреднённая по классам, реально встретившимся как истинная метка
    (support>0) — так же, как sklearn.metrics.precision_score(average='macro')
    по умолчанию считает по классам из y_true."""
    tp = cm.diag().float()
    predicted_positive = cm.sum(dim=0).float()  # столбцы = сколько раз класс c был ПРЕДСКАЗАН
    support = cm.sum(dim=1)  # строки = сколько раз класс c был ИСТИННЫМ
    precision_per_class = torch.where(predicted_positive > 0, tp / predicted_positive.clamp(min=1), torch.zeros_like(tp))
    mask = support > 0
    if mask.sum().item() == 0:
        return 0.0
    return precision_per_class[mask].mean().item()


def evaluate_metrics(
    model: SyscallLSTM,
    loader: DataLoader,
    device: torch.device,
    vocab_size_syscall: int,
    vocab_size_process: int,
    max_batches: int | None = None,
) -> dict[str, float]:
    """Полный eval-проход (model.eval(), без dropout/backward): loss +
    macro-precision + perplexity (=exp(loss), бесплатно) для КАЖДОЙ головы.

    Используется и для train (после эпохи — "чистая" метрика без влияния
    dropout/оптимизатора, поэтому обычно чуть лучше "живого" running loss во
    время самого обучения), и для val — единая функция, чтобы кривые были
    сравнимы.

    max_batches — если задан, останавливается после первых N батчей loader'а
    (см. config.TRAIN_METRICS_MAX_BATCHES — компромисс точность/скорость на
    большом train, который иначе гонять целиком каждые N эпох дорого)."""
    model.eval()
    total_loss_syscall = 0.0
    total_loss_process = 0.0
    total_steps = 0
    cm_syscall = torch.zeros(vocab_size_syscall, vocab_size_syscall, dtype=torch.long)
    cm_process = torch.zeros(vocab_size_process, vocab_size_process, dtype=torch.long)

    with torch.no_grad():
        for batch_idx, (x, y) in enumerate(loader):
            if max_batches is not None and batch_idx >= max_batches:
                break
            x, y = x.to(device), y.to(device)
            logits_syscall, logits_process = model(x)

            target_syscall = y[..., 0].reshape(-1)
            loss_syscall = F.cross_entropy(logits_syscall.reshape(-1, logits_syscall.size(-1)), target_syscall, reduction="sum")
            total_loss_syscall += loss_syscall.item()
            total_steps += target_syscall.numel()
            pred_syscall = logits_syscall.argmax(dim=-1).reshape(-1)
            _update_confusion(cm_syscall, target_syscall.cpu(), pred_syscall.cpu(), vocab_size_syscall)

            target_process = y[..., 1].reshape(-1)
            loss_process = F.cross_entropy(logits_process.reshape(-1, logits_process.size(-1)), target_process, reduction="sum")
            total_loss_process += loss_process.item()
            pred_process = logits_process.argmax(dim=-1).reshape(-1)
            _update_confusion(cm_process, target_process.cpu(), pred_process.cpu(), vocab_size_process)

    loss_syscall = total_loss_syscall / total_steps
    loss_process = total_loss_process / total_steps
    return {
        "loss_syscall": loss_syscall,
        "perplexity_syscall": float(np.exp(loss_syscall)),
        "precision_syscall": _macro_precision_from_confusion(cm_syscall),
        "loss_process": loss_process,
        "perplexity_process": float(np.exp(loss_process)),
        "precision_process": _macro_precision_from_confusion(cm_process),
    }



def calibrate_threshold(model: SyscallLSTM, val_loader: DataLoader, device: torch.device) -> float:
    """Порог тревоги = config.THRESHOLD_PERCENTILE-й перцентиль anomaly
    score (syscall + config.PROCESS_SCORE_WEIGHT * process) по окнам НА
    VAL-СПЛИТЕ (held-out нормальные данные — модель их не видела на train,
    но они гарантированно без атак)."""
    model.eval()
    scores: list[float] = []
    with torch.no_grad():
        for x, y in val_loader:
            x, y = x.to(device), y.to(device)
            logits_syscall, logits_process = model(x)
            syscall_scores, process_scores = compute_step_scores_components(
                logits_syscall, logits_process, y, method=config.SCORE_METHOD, top_k=config.TOP_K
            )
            combined = combine_step_scores(syscall_scores, process_scores, process_weight=config.PROCESS_SCORE_WEIGHT)
            window_scores = aggregate_window_scores(combined, window_agg=config.WINDOW_AGG, window_agg_quantile=config.WINDOW_AGG_QUANTILE)
            scores.extend(window_scores.cpu().tolist())
    return float(np.percentile(scores, config.THRESHOLD_PERCENTILE))



def quick_test_evaluation(
    model: SyscallLSTM, test_loader: DataLoader, threshold: float, device: torch.device
) -> None:
    """Diagnostics-оценка на test-сплите: печатает classification_report
    (окно-атака vs окно-норма, предсказано по threshold, score = syscall +
    config.PROCESS_SCORE_WEIGHT * process, агрегация — config.WINDOW_AGG) и
    ROC-AUC.

    Заодно, БЕСПЛАТНО (те же логиты, никаких лишних forward-проходов),
    сравнивает AUC для трёх составов score: только syscall, только process,
    комбинированный (текущий вес) — это отвечает на вопрос "действительно
    ли process-голова помогает поймать ЭТУ атаку, или весь сигнал всё равно
    идёт от syscall". Если "только process" даёт AUC заметно выше "только
    syscall" — атака в этом сценарии, видимо, проявляется именно как
    аномальный процесс (например web-shell/RCE), а не необычная
    последовательность syscall'ов.
    """
    model.eval()
    syscall_steps_parts: list[torch.Tensor] = []
    process_steps_parts: list[torch.Tensor] = []
    truth: list[bool] = []
    with torch.no_grad():
        for x, y, window_is_attack in test_loader:
            x, y = x.to(device), y.to(device)
            logits_syscall, logits_process = model(x)
            s_syscall, s_process = compute_step_scores_components(
                logits_syscall, logits_process, y, method=config.SCORE_METHOD, top_k=config.TOP_K
            )
            syscall_steps_parts.append(s_syscall.cpu())
            process_steps_parts.append(s_process.cpu())
            truth.extend(window_is_attack.tolist() if torch.is_tensor(window_is_attack) else list(window_is_attack))

    if not truth:
        print("test-сплит пуст — пропускаю diagnostics-оценку")
        return

    syscall_steps = torch.cat(syscall_steps_parts, dim=0)
    process_steps = torch.cat(process_steps_parts, dim=0)
    combined_steps = combine_step_scores(syscall_steps, process_steps, process_weight=config.PROCESS_SCORE_WEIGHT)

    def agg(steps: torch.Tensor) -> list[float]:
        return aggregate_window_scores(steps, window_agg=config.WINDOW_AGG, window_agg_quantile=config.WINDOW_AGG_QUANTILE).tolist()

    combined_scores = agg(combined_steps)
    predicted_attack = [s > threshold for s in combined_scores]

    print(f"(агрегация окна: {config.WINDOW_AGG}, score = syscall + {config.PROCESS_SCORE_WEIGHT}×process)")
    print(classification_report(truth, predicted_attack, target_names=["Normal", "Attack"], digits=3, zero_division=0))
    if len(set(truth)) == 2:
        auc = roc_auc_score(truth, combined_scores)
        print(f"ROC-AUC (комбинированный score): {auc:.4f}")

        print("Сравнение AUC по составу score (та же агрегация окна, без переобучения):")
        components = [
            ("только syscall", syscall_steps),
            ("только process", process_steps),
            (f"syscall + {config.PROCESS_SCORE_WEIGHT}×process (текущий)", combined_steps),
        ]
        for name, steps in components:
            comp_auc = roc_auc_score(truth, agg(steps))
            print(f"  {name:<45} AUC={comp_auc:.4f}")
    else:
        print("В test-сплите присутствует только один класс окон — ROC-AUC не считается")


def load_resume_checkpoint(
    service_name: str, checkpoint_path: str, vocab_sizes: dict[str, int], device: torch.device
) -> dict | None:
    """Если config.RESUME=True и для сервиса уже есть СОВМЕСТИМЫЙ чекпоинт —
    возвращает сырой checkpoint dict (torch.load), иначе None (обучение с
    нуля). Намеренно НЕ трогает модель/оптимизатор — на момент этого вызова
    модель ещё не создана: архитектура (ModelHParams) должна быть определена
    из checkpoint ДО конструирования SyscallLSTM, иначе получаем тот самый
    баг, ради исправления которого всё это писалось (модель строится под
    текущий config.py, а веса в чекпоинте — под другой).

    Совместимость проверяется по трём вещам:
    - architecture_version: старые (однобашенные) чекпоинты структурно
      несовместимы с текущей моделью (другой набор слоёв: output_syscall +
      output_process вместо одного output) — load_state_dict упал бы с
      неинформативной ошибкой mismatch'а ключей, поэтому проверяем явно;
    - vocab_sizes: иначе размеры Embedding-слоёв не совпадут;
    - use_arg_count_feature: он не только часть архитектуры, но и меняет
      ШИРИНУ входного вектора признаков в encode_line (data.py), которая
      берётся из живого config.py при построении train/val-последовательностей
      — если он отличается от чекпоинта, дообучение невозможно даже если
      остальные гиперпараметры совпадают.
    """
    if not config.RESUME:
        return None

    if not os.path.exists(checkpoint_path):
        print(f"[{service_name}] config.RESUME=True, но чекпоинт {checkpoint_path} не найден — обучение с нуля")
        return None

    checkpoint = torch.load(checkpoint_path, map_location=device)

    if checkpoint.get("architecture_version") != ARCHITECTURE_VERSION:
        print(
            f"[{service_name}] ВНИМАНИЕ: чекпоинт сохранён архитектурой версии "
            f"{checkpoint.get('architecture_version')!r}, текущий код — версии {ARCHITECTURE_VERSION} "
            f"(скорее всего это старый однобашенный чекпоинт без process-головы) — "
            f"дообучение невозможно, начинаю с нуля."
        )
        return None

    if checkpoint["vocab_sizes"] != vocab_sizes:
        print(
            f"[{service_name}] ВНИМАНИЕ: vocab_sizes в чекпоинте {checkpoint['vocab_sizes']} "
            f"не совпадает с текущим {vocab_sizes} (изменился train-сплит или config?) — "
            f"дообучение невозможно, начинаю с нуля."
        )
        return None

    checkpoint_hparams = ModelHParams.from_checkpoint(checkpoint)
    if checkpoint_hparams.use_arg_count_feature != config.USE_ARG_COUNT_FEATURE:
        print(
            f"[{service_name}] ВНИМАНИЕ: use_arg_count_feature в чекпоинте "
            f"({checkpoint_hparams.use_arg_count_feature}) не совпадает с текущим "
            f"config.USE_ARG_COUNT_FEATURE ({config.USE_ARG_COUNT_FEATURE}) — это меняет ширину "
            f"входного вектора признаков, дообучение невозможно, начинаю с нуля."
        )
        return None

    if checkpoint_hparams != ModelHParams.from_config():
        print(
            f"[{service_name}] гиперпараметры чекпоинта отличаются от текущего config.py — "
            f"продолжаю обучение с АРХИТЕКТУРОЙ ИЗ ЧЕКПОИНТА (config.py для архитектуры игнорируется "
            f"в этом запуске): {checkpoint_hparams}"
        )

    return checkpoint


def calibrate_and_evaluate(
    service_name: str,
    model: SyscallLSTM,
    val_loader: DataLoader,
    test_loader: DataLoader | None,
    device: torch.device,
    epoch_label: str | None = None,
) -> float:
    """Калибрует порог на val и (если test_loader доступен) сразу гоняет
    diagnostics-оценку на test — общая логика для "после каждой эпохи" и
    "после последней эпохи" веток в train_one_service."""
    threshold = calibrate_threshold(model, val_loader, device)
    prefix = f"[{service_name}]" + (f" ({epoch_label})" if epoch_label else "")
    print(
        f"{prefix} порог тревоги ({config.SCORE_METHOD}, "
        f"{config.THRESHOLD_PERCENTILE}-й перцентиль val): {threshold:.4f}"
    )
    if test_loader is not None:
        print(f"{prefix} diagnostics-оценка на test-сплите:")
        quick_test_evaluation(model, test_loader, threshold, device)
    return threshold


def train_one_service(service_name: str, device: torch.device) -> None:
    print(f"\n=== Сервис: {service_name} ===")

    vocabs = build_vocab(service_name, use_cache=not config.FORCE_REBUILD_VOCAB)
    vocab_sizes = {name: len(vocab) for name, vocab in vocabs.items()}
    if config.USE_ARG_COUNT_FEATURE:
        vocab_sizes["arg_count"] = config.ARG_COUNT_BUCKETS
    print(f"vocab_sizes={vocab_sizes}")

    X_train, y_train = build_normal_sequences(service_name, vocabs, "train", config.SEQ_LEN, config.SEQ_STEP)
    X_val, y_val = build_normal_sequences(service_name, vocabs, "val", config.SEQ_LEN, config.SEQ_STEP)
    print(f"train-последовательностей: {len(X_train)}  val-последовательностей: {len(X_val)}")

    if len(X_train) == 0 or len(X_val) == 0:
        print(f"[{service_name}] недостаточно данных в train/val (короче SEQ_LEN+1) — пропускаю")
        return

    train_loader = DataLoader(SequenceDataset(X_train, y_train), batch_size=config.BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(SequenceDataset(X_val, y_val), batch_size=config.BATCH_SIZE, shuffle=False)

    # test-сплит строится ОДИН раз и переиспользуется на всех эпохах (не
    # только на последней) — только для diagnostics, сама модель эти данные
    # никогда не видит на обучении.
    X_test, y_test, window_is_attack = build_test_sequences(service_name, vocabs, config.SEQ_LEN, config.SEQ_LEN)
    test_loader: DataLoader | None = None
    if len(X_test):
        test_loader = DataLoader(EvalSequenceDataset(X_test, y_test, window_is_attack), batch_size=config.BATCH_SIZE, shuffle=False)
    else:
        print(f"[{service_name}] test-сплит пуст или короче SEQ_LEN+1 — diagnostics-оценка недоступна")

    checkpoint_path = os.path.join(config.MODEL_DIR, f"{service_name}.pt")

    # ВАЖНО: чекпоинт проверяется и его hparams определяются ДО создания
    # модели/оптимизатора — модель должна строиться под архитектуру
    # чекпоинта (если дообучаем), а не под текущий config.py, иначе
    # load_state_dict ниже упадёт при их рассинхроне.
    resume_checkpoint = load_resume_checkpoint(service_name, checkpoint_path, vocab_sizes, device)
    hparams = ModelHParams.from_checkpoint(resume_checkpoint) if resume_checkpoint is not None else ModelHParams.from_config()

    model = SyscallLSTM(vocab_sizes, hparams=hparams).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.LEARNING_RATE)

    start_epoch = 0
    if resume_checkpoint is not None:
        model.load_state_dict(resume_checkpoint["model_state"])
        if "optimizer_state" in resume_checkpoint:
            optimizer.load_state_dict(resume_checkpoint["optimizer_state"])
        start_epoch = resume_checkpoint.get("epochs_trained", 0)
        print(f"[{service_name}] дообучаю с эпохи {start_epoch + 1} (чекпоинт: {checkpoint_path})")

    if start_epoch >= config.EPOCHS:
        print(
            f"[{service_name}] чекпоинт уже обучен на {start_epoch} эпох >= config.EPOCHS={config.EPOCHS} — "
            f"увеличьте config.EPOCHS, чтобы дообучить дальше. Пропускаю обучение, но всё равно "
            f"пересчитаю порог/diagnostics и пересохраню чекпоинт."
        )

    threshold: float | None = None
    history: dict[str, list[float]] = {
        "epoch": [],
        "train_loss_syscall": [], "val_loss_syscall": [],
        "train_precision_syscall": [], "val_precision_syscall": [],
        "train_loss_process": [], "val_loss_process": [],
        "train_precision_process": [], "val_precision_process": [],
    }

    for epoch in range(start_epoch, config.EPOCHS):
        model.train()
        total_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            logits_syscall, logits_process = model(x)
            loss_syscall = F.cross_entropy(logits_syscall.reshape(-1, logits_syscall.size(-1)), y[..., 0].reshape(-1))
            loss_process = F.cross_entropy(logits_process.reshape(-1, logits_process.size(-1)), y[..., 1].reshape(-1))
            loss = loss_syscall + config.PROCESS_LOSS_WEIGHT * loss_process
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        epoch_num = epoch + 1
        running_train_loss = total_loss / len(train_loader)
        is_last_epoch = epoch == config.EPOCHS - 1
        is_metrics_epoch = (epoch_num % config.METRICS_EVAL_EVERY_N_EPOCHS == 0) or is_last_epoch

        if is_metrics_epoch:
            # Полный eval-проход ОТДЕЛЬНО по train (max_batches — см.
            # config.TRAIN_METRICS_MAX_BATCHES, на большом train это дорого)
            # и по val (всегда целиком — val обычно намного меньше train).
            train_metrics = evaluate_metrics(
                model, train_loader, device, vocab_sizes["syscall"], vocab_sizes["process"],
                max_batches=config.TRAIN_METRICS_MAX_BATCHES,
            )
            val_metrics = evaluate_metrics(model, val_loader, device, vocab_sizes["syscall"], vocab_sizes["process"])

            print(
                f"[{service_name}] эпоха {epoch_num}/{config.EPOCHS}  running_train_loss={running_train_loss:.4f}\n"
                f"  train: loss(syscall)={train_metrics['loss_syscall']:.4f} "
                f"precision(syscall)={train_metrics['precision_syscall']:.3f} "
                f"loss(process)={train_metrics['loss_process']:.4f} "
                f"precision(process)={train_metrics['precision_process']:.3f}\n"
                f"  val:   loss(syscall)={val_metrics['loss_syscall']:.4f} "
                f"precision(syscall)={val_metrics['precision_syscall']:.3f} "
                f"loss(process)={val_metrics['loss_process']:.4f} "
                f"precision(process)={val_metrics['precision_process']:.3f}"
            )

            history["epoch"].append(epoch_num)
            history["train_loss_syscall"].append(train_metrics["loss_syscall"])
            history["val_loss_syscall"].append(val_metrics["loss_syscall"])
            history["train_precision_syscall"].append(train_metrics["precision_syscall"])
            history["val_precision_syscall"].append(val_metrics["precision_syscall"])
            history["train_loss_process"].append(train_metrics["loss_process"])
            history["val_loss_process"].append(val_metrics["loss_process"])
            history["train_precision_process"].append(train_metrics["precision_process"])
            history["val_precision_process"].append(val_metrics["precision_process"])
        else:
            print(f"[{service_name}] эпоха {epoch_num}/{config.EPOCHS}  running_train_loss={running_train_loss:.4f}")

        resource_guard.check_ram(f"{service_name}: конец эпохи {epoch_num}")

        if config.EVAL_TEST_EVERY_EPOCH or is_last_epoch:
            threshold = calibrate_and_evaluate(
                service_name, model, val_loader, test_loader, device,
                epoch_label=f"эпоха {epoch_num}/{config.EPOCHS}",
            )

    if history["epoch"]:
        plot_path = plot_training_curves(service_name, history)
        if plot_path:
            print(f"[{service_name}] график метрик по эпохам сохранён в {plot_path}")

    if threshold is None:
        # Цикл выше не выполнился ни разу (чекпоинт уже обучен на
        # config.EPOCHS+ эпох) — порог/diagnostics всё равно нужно посчитать
        # хотя бы раз, иначе нечего будет сохранить в чекпоинт.
        threshold = calibrate_and_evaluate(service_name, model, val_loader, test_loader, device)

    os.makedirs(config.MODEL_DIR, exist_ok=True)
    torch.save(
        {
            "architecture_version": ARCHITECTURE_VERSION,
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "epochs_trained": max(start_epoch, config.EPOCHS),
            "vocabs": vocabs,
            "vocab_sizes": vocab_sizes,
            "feature_order": model.feature_order,
            # Источник истины для архитектуры при следующей загрузке/дообучении
            # (см. model.ModelHParams) — берём из САМОЙ модели (model.hparams),
            # а не заново из config.py, чтобы при RESUME с чужими hparams в
            # чекпоинте не перезаписать их текущими значениями config.py.
            "hparams": model.hparams.to_dict(),
            "seq_len": config.SEQ_LEN,
            "score_method": config.SCORE_METHOD,
            "top_k": config.TOP_K,
            "window_agg": config.WINDOW_AGG,
            "window_agg_quantile": config.WINDOW_AGG_QUANTILE,
            "process_score_weight": config.PROCESS_SCORE_WEIGHT,
            "threshold": threshold,
            "service_name": service_name,
        },
        checkpoint_path,
    )
    print(f"[{service_name}] модель сохранена в {checkpoint_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--service", help="Обучить только один сервис (по умолчанию — все из config.LID_DS_ROOT)")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    services = [args.service] if args.service else list_services()
    print(f"Устройство: {device}")
    print(f"Сервисы: {services}")

    for service_name in services:
        train_one_service(service_name, device)
        # На случай нескольких сервисов подряд в одном процессе: явно чистим
        # мусор между ними (X_train/X_val/DataLoader'ы предыдущего сервиса
        # должны быть уже недостижимы) и логируем RAM, чтобы было видно,
        # накапливается что-то между сервисами или нет.
        gc.collect()
        resource_guard.check_ram(f"после сервиса {service_name}")


if __name__ == "__main__":
    main()