"""Навчання per-service LSTM для next-syscall.

    train-спліт (чисто нормальний) -> навчання моделі передбачати
        наступний syscall
    val-спліт (чисто нормальний, held-out) -> калібрування порогу тривоги
        (config.THRESHOLD_PERCENTILE-й перцентиль anomaly score)
    test-спліт (норма+атаки) -> швидка diagnostics-оцінка (precision/
        recall/AUC за вікнами, використовуючи відому розмітку атак тільки для
        оцінки — модель її ніколи не бачить під час навчання)
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
    """cm: [num_classes, num_classes] (рядки — істина, стовпці — передбачення),
    акумулюється за батчами через bincount """
    idx = y_true.reshape(-1).long() * num_classes + y_pred.reshape(-1).long()
    cm += torch.bincount(idx, minlength=num_classes * num_classes).reshape(num_classes, num_classes)


def _macro_precision_from_confusion(cm: torch.Tensor) -> float:
    """Macro-precision за накопиченою confusion matrix: TP_c/(TP_c+FP_c) на
    клас, усереднена за класами, що реально зустрілися як істинна мітка
    (support>0) — так само, як sklearn.metrics.precision_score(average='macro')
    за замовчуванням рахує за класами з y_true."""
    tp = cm.diag().float()
    predicted_positive = cm.sum(dim=0).float()  # стовпці = скільки разів клас c був ПЕРЕДБАЧЕНИЙ
    support = cm.sum(dim=1)  # рядки = скільки разів клас c був ІСТИННИМ
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
    """Повний eval-прохід (model.eval(), без dropout/backward): loss +
    macro-precision + perplexity (=exp(loss), безкоштовно) для КОЖНОЇ голови.

    Використовується і для train (після епохи — "чиста" метрика без впливу
    dropout/оптимізатора, тому зазвичай трохи краща за "живий" running loss під
    час самого навчання), і для val — єдина функція, щоб криві були
    порівнянними.

    max_batches — якщо заданий, зупиняється після перших N батчів loader'а
    (див. config.TRAIN_METRICS_MAX_BATCHES — компроміс точність/швидкість на
    великому train, який інакше ганяти цілком кожні N епох дорого)."""
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
    """Поріг тривоги = config.THRESHOLD_PERCENTILE-й перцентиль anomaly
    score (syscall + config.PROCESS_SCORE_WEIGHT * process) за вікнами НА
    VAL-СПЛІТІ (held-out нормальні дані — модель їх не бачила на train,
    але вони гарантовано без атак)."""
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
    """Diagnostics-оцінка на test-спліті: друкує classification_report
    (вікно-атака vs вікно-норма, передбачено за threshold, score = syscall +
    config.PROCESS_SCORE_WEIGHT * process, агрегація — config.WINDOW_AGG) і
    ROC-AUC.

    Заодно, БЕЗКОШТОВНО (ті ж логіти, ніяких зайвих forward-проходів),
    порівнює AUC для трьох складів score: тільки syscall, тільки process,
    комбінований (поточна вага) — це відповідає на питання "чи дійсно
    process-голова допомагає спіймати ЦЮ атаку, чи весь сигнал все одно
    йде від syscall". Якщо "тільки process" дає AUC помітно вище "тільки
    syscall" — атака в цьому сценарії, мабуть, проявляється саме як
    аномальний процес (наприклад web-shell/RCE), а не незвичайна
    послідовність syscall'ів.
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
        print("test-спліт порожній — пропускаю diagnostics-оцінку")
        return

    syscall_steps = torch.cat(syscall_steps_parts, dim=0)
    process_steps = torch.cat(process_steps_parts, dim=0)
    combined_steps = combine_step_scores(syscall_steps, process_steps, process_weight=config.PROCESS_SCORE_WEIGHT)

    def agg(steps: torch.Tensor) -> list[float]:
        return aggregate_window_scores(steps, window_agg=config.WINDOW_AGG, window_agg_quantile=config.WINDOW_AGG_QUANTILE).tolist()

    combined_scores = agg(combined_steps)
    predicted_attack = [s > threshold for s in combined_scores]

    print(f"(агрегація вікна: {config.WINDOW_AGG}, score = syscall + {config.PROCESS_SCORE_WEIGHT}×process)")
    print(classification_report(truth, predicted_attack, target_names=["Normal", "Attack"], digits=3, zero_division=0))
    if len(set(truth)) == 2:
        auc = roc_auc_score(truth, combined_scores)
        print(f"ROC-AUC (комбінований score): {auc:.4f}")

        print("Порівняння AUC за складом score (та сама агрегація вікна, без перенавчання):")
        components = [
            ("тільки syscall", syscall_steps),
            ("тільки process", process_steps),
            (f"syscall + {config.PROCESS_SCORE_WEIGHT}×process (поточний)", combined_steps),
        ]
        for name, steps in components:
            comp_auc = roc_auc_score(truth, agg(steps))
            print(f"  {name:<45} AUC={comp_auc:.4f}")
    else:
        print("У test-спліті присутній тільки один клас вікон — ROC-AUC не рахується")


def load_resume_checkpoint(
    service_name: str, checkpoint_path: str, vocab_sizes: dict[str, int], device: torch.device
) -> dict | None:
    """Якщо config.RESUME=True і для сервісу вже є СУМІСНИЙ чекпоінт —
    повертає сирий checkpoint dict (torch.load), інакше None (навчання з
    нуля). Навмисно НЕ чіпає модель/оптимізатор — на момент цього виклику
    модель ще не створена: архітектура (ModelHParams) має бути визначена
    з checkpoint ДО конструювання SyscallLSTM, інакше отримуємо той самий
    баг, заради виправлення якого все це писалося (модель будується під
    поточний config.py, а ваги в чекпоінті — під інший).

    Сумісність перевіряється за трьома речами:
    - architecture_version: старі (однобаштові) чекпоінти структурно
      несумісні з поточною моделлю (інший набір шарів: output_syscall +
      output_process замість одного output) — load_state_dict впав би з
      неінформативною помилкою mismatch'у ключів, тому перевіряємо явно;
    - vocab_sizes: інакше розміри Embedding-шарів не співпадуть;
    - use_arg_count_feature: він не тільки частина архітектури, але й змінює
      ШИРИНУ вхідного вектора ознак у encode_line (data.py), яка
      береться з живого config.py під час побудови train/val-послідовностей
      — якщо він відрізняється від чекпоінта, донавчання неможливе навіть якщо
      інші гіперпараметри збігаються.
    """
    if not config.RESUME:
        return None

    if not os.path.exists(checkpoint_path):
        print(f"[{service_name}] config.RESUME=True, але чекпоінт {checkpoint_path} не знайдено — навчання з нуля")
        return None

    checkpoint = torch.load(checkpoint_path, map_location=device)

    if checkpoint.get("architecture_version") != ARCHITECTURE_VERSION:
        print(
            f"[{service_name}] УВАГА: чекпоінт збережено архітектурою версії "
            f"{checkpoint.get('architecture_version')!r}, поточний код — версії {ARCHITECTURE_VERSION} "
            f"(швидше за все це старий однобаштовий чекпоінт без process-голови) — "
            f"донавчання неможливе, починаю з нуля."
        )
        return None

    if checkpoint["vocab_sizes"] != vocab_sizes:
        print(
            f"[{service_name}] УВАГА: vocab_sizes у чекпоінті {checkpoint['vocab_sizes']} "
            f"не збігається з поточним {vocab_sizes} (змінився train-спліт або config?) — "
            f"донавчання неможливе, починаю з нуля."
        )
        return None

    checkpoint_hparams = ModelHParams.from_checkpoint(checkpoint)
    if checkpoint_hparams.use_arg_count_feature != config.USE_ARG_COUNT_FEATURE:
        print(
            f"[{service_name}] УВАГА: use_arg_count_feature у чекпоінті "
            f"({checkpoint_hparams.use_arg_count_feature}) не збігається з поточним "
            f"config.USE_ARG_COUNT_FEATURE ({config.USE_ARG_COUNT_FEATURE}) — це змінює ширину "
            f"вхідного вектора ознак, донавчання неможливе, починаю з нуля."
        )
        return None

    if checkpoint_hparams != ModelHParams.from_config():
        print(
            f"[{service_name}] гіперпараметри чекпоінта відрізняються від поточного config.py — "
            f"продовжую навчання з АРХІТЕКТУРОЮ З ЧЕКПОІНТА (config.py для архітектури ігнорується "
            f"в цьому запуску): {checkpoint_hparams}"
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
    """Калібрує поріг на val і (якщо test_loader доступний) одразу ганяє
    diagnostics-оцінку на test — загальна логіка для "після кожної епохи" та
    "після останньої епохи" гілок у train_one_service."""
    threshold = calibrate_threshold(model, val_loader, device)
    prefix = f"[{service_name}]" + (f" ({epoch_label})" if epoch_label else "")
    print(
        f"{prefix} поріг тривоги ({config.SCORE_METHOD}, "
        f"{config.THRESHOLD_PERCENTILE}-й перцентиль val): {threshold:.4f}"
    )
    if test_loader is not None:
        print(f"{prefix} diagnostics-оцінка на test-спліті:")
        quick_test_evaluation(model, test_loader, threshold, device)
    return threshold


def train_one_service(service_name: str, device: torch.device) -> None:
    print(f"\n=== Сервіс: {service_name} ===")

    vocabs = build_vocab(service_name, use_cache=not config.FORCE_REBUILD_VOCAB)
    vocab_sizes = {name: len(vocab) for name, vocab in vocabs.items()}
    if config.USE_ARG_COUNT_FEATURE:
        vocab_sizes["arg_count"] = config.ARG_COUNT_BUCKETS
    print(f"vocab_sizes={vocab_sizes}")

    X_train, y_train = build_normal_sequences(service_name, vocabs, "train", config.SEQ_LEN, config.SEQ_STEP)
    X_val, y_val = build_normal_sequences(service_name, vocabs, "val", config.SEQ_LEN, config.SEQ_STEP)
    print(f"train-послідовностей: {len(X_train)}  val-послідовностей: {len(X_val)}")

    if len(X_train) == 0 or len(X_val) == 0:
        print(f"[{service_name}] недостатньо даних у train/val (коротше SEQ_LEN+1) — пропускаю")
        return

    train_loader = DataLoader(SequenceDataset(X_train, y_train), batch_size=config.BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(SequenceDataset(X_val, y_val), batch_size=config.BATCH_SIZE, shuffle=False)

    # test-спліт будується ОДИН раз і перевикористовується на всіх епохах (не
    # тільки на останній) — тільки для diagnostics, сама модель ці дані
    # ніколи не бачить на навчанні.
    X_test, y_test, window_is_attack = build_test_sequences(service_name, vocabs, config.SEQ_LEN, config.SEQ_LEN)
    test_loader: DataLoader | None = None
    if len(X_test):
        test_loader = DataLoader(EvalSequenceDataset(X_test, y_test, window_is_attack), batch_size=config.BATCH_SIZE, shuffle=False)
    else:
        print(f"[{service_name}] test-спліт порожній або коротший за SEQ_LEN+1 — diagnostics-оцінка недоступна")

    checkpoint_path = os.path.join(config.MODEL_DIR, f"{service_name}.pt")

    # ВАЖЛИВО: чекпоінт перевіряється і його hparams визначаються ДО створення
    # моделі/оптимізатора — модель повинна будуватися під архітектуру
    # чекпоінта (якщо донавчаємо), а не під поточний config.py, інакше
    # load_state_dict нижче впаде при їх розсинхроні.
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
        print(f"[{service_name}] донавчаю з епохи {start_epoch + 1} (чекпоінт: {checkpoint_path})")

    if start_epoch >= config.EPOCHS:
        print(
            f"[{service_name}] чекпоінт вже навчений на {start_epoch} епох >= config.EPOCHS={config.EPOCHS} — "
            f"збільште config.EPOCHS, щоб донавчити далі. Пропускаю навчання, але все одно "
            f"перерахую поріг/diagnostics і перезбережу чекпоінт."
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
            # Повний eval-прохід ОКРЕМО по train (max_batches — див.
            # config.TRAIN_METRICS_MAX_BATCHES, на великому train це дорого)
            # і по val (завжди цілком — val зазвичай набагато менший за train).
            train_metrics = evaluate_metrics(
                model, train_loader, device, vocab_sizes["syscall"], vocab_sizes["process"],
                max_batches=config.TRAIN_METRICS_MAX_BATCHES,
            )
            val_metrics = evaluate_metrics(model, val_loader, device, vocab_sizes["syscall"], vocab_sizes["process"])

            print(
                f"[{service_name}] епоха {epoch_num}/{config.EPOCHS}  running_train_loss={running_train_loss:.4f}\n"
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
            print(f"[{service_name}] епоха {epoch_num}/{config.EPOCHS}  running_train_loss={running_train_loss:.4f}")

        resource_guard.check_ram(f"{service_name}: кінець епохи {epoch_num}")

        if config.EVAL_TEST_EVERY_EPOCH or is_last_epoch:
            threshold = calibrate_and_evaluate(
                service_name, model, val_loader, test_loader, device,
                epoch_label=f"епоха {epoch_num}/{config.EPOCHS}",
            )

    if history["epoch"]:
        plot_path = plot_training_curves(service_name, history)
        if plot_path:
            print(f"[{service_name}] графік метрик за епохами збережено у {plot_path}")

    if threshold is None:
        # Цикл вище не виконався жодного разу (чекпоінт вже навчений на
        # config.EPOCHS+ епох) — поріг/diagnostics все одно потрібно порахувати
        # хоча б раз, інакше нічого буде зберегти в чекпоінт.
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
            # Джерело істини для архітектури при наступному завантаженні/донавчанні
            # (див. model.ModelHParams) — беремо із САМОЇ моделі (model.hparams),
            # а не заново з config.py, щоб при RESUME з чужими hparams у
            # чекпоінті не перезаписати їх поточними значеннями config.py.
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
    print(f"[{service_name}] модель збережена у {checkpoint_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--service", help="Навчити тільки один сервіс (за замовчуванням — усі з config.LID_DS_ROOT)")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    services = [args.service] if args.service else list_services()
    print(f"Пристрій: {device}")
    print(f"Сервіси: {services}")

    for service_name in services:
        train_one_service(service_name, device)
        # На випадок кількох сервісів поспіль в одному процесі: явно чистимо
        # сміття між ними (X_train/X_val/DataLoader'и попереднього сервісу
        # мають бути вже недосяжними) і логуємо RAM, щоб було видно,
        # накопичується щось між сервісами чи ні.
        gc.collect()
        resource_guard.check_ram(f"після сервісу {service_name}")


if __name__ == "__main__":
    main()