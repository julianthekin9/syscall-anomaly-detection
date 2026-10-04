import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import classification_report, roc_auc_score
from torch.utils.data import DataLoader

from syscall_hids import config
from syscall_hids.modules.models import SyscallLSTM
from syscall_hids.modules.scoring import aggregate_window_scores, compute_step_scores
from syscall_hids.tools.visualization import plot_roc_curve

def _update_confusion(cm: torch.Tensor, y_true: torch.Tensor, y_pred: torch.Tensor, num_classes: int) -> None:
    idx = y_true.reshape(-1).long() * num_classes + y_pred.reshape(-1).long()
    cm += torch.bincount(idx, minlength=num_classes * num_classes).reshape(num_classes, num_classes)


def _macro_precision_from_confusion(cm: torch.Tensor) -> float:
    tp = cm.diag().float()
    predicted_positive = cm.sum(dim=0).float()
    support = cm.sum(dim=1)
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
    max_batches: int | None = None,
) -> dict[str, float]:
    model.eval()
    total_loss_syscall = 0.0
    total_steps = 0
    cm_syscall = torch.zeros(vocab_size_syscall, vocab_size_syscall, dtype=torch.long)

    with torch.no_grad():
        for batch_idx, (x, y) in enumerate(loader):
            if max_batches is not None and batch_idx >= max_batches:
                break
            x, y = x.to(device), y.to(device)
            logits_syscall = model(x)

            target_syscall = y[..., 0].reshape(-1)
            loss_syscall = F.cross_entropy(
                logits_syscall.reshape(-1, logits_syscall.size(-1)), target_syscall, reduction="sum"
            )
            total_loss_syscall += loss_syscall.item()
            total_steps += target_syscall.numel()
            pred_syscall = logits_syscall.argmax(dim=-1).reshape(-1)
            _update_confusion(cm_syscall, target_syscall.cpu(), pred_syscall.cpu(), vocab_size_syscall)

    loss_syscall = total_loss_syscall / total_steps
    return {
        "loss_syscall": loss_syscall,
        "perplexity_syscall": float(np.exp(loss_syscall)),
        "precision_syscall": _macro_precision_from_confusion(cm_syscall),
    }


def calibrate_threshold(model: SyscallLSTM, val_loader: DataLoader, device: torch.device) -> float:
    model.eval()
    scores: list[float] = []
    with torch.no_grad():
        for x, y in val_loader:
            x, y = x.to(device), y.to(device)
            logits_syscall = model(x)
            step_scores = compute_step_scores(logits_syscall, y)
            window_scores = aggregate_window_scores(
                step_scores, window_agg=config.WINDOW_AGG, window_agg_quantile=config.WINDOW_AGG_QUANTILE
            )
            scores.extend(window_scores.cpu().tolist())
    return float(np.percentile(scores, config.THRESHOLD_PERCENTILE))


def quick_test_evaluation(
    model: SyscallLSTM,
    test_loader: DataLoader,
    threshold: float,
    device: torch.device,
    service_name: str,
    roc_tags: tuple[str, ...],
) -> None:
    model.eval()
    steps_parts: list[torch.Tensor] = []
    truth: list[bool] = []
    with torch.no_grad():
        for x, y, window_is_attack in test_loader:
            x, y = x.to(device), y.to(device)
            logits_syscall = model(x)
            step_scores = compute_step_scores(logits_syscall, y)
            steps_parts.append(step_scores.cpu())
            truth.extend(window_is_attack.tolist() if torch.is_tensor(window_is_attack) else list(window_is_attack))

    if not truth:
        print("test-спліт порожній — пропускаю diagnostics-оцінку")
        return

    all_steps = torch.cat(steps_parts, dim=0)
    window_scores = aggregate_window_scores(
        all_steps, window_agg=config.WINDOW_AGG, window_agg_quantile=config.WINDOW_AGG_QUANTILE
    ).tolist()
    predicted_attack = [s > threshold for s in window_scores]

    print(f"(агрегація вікна: {config.WINDOW_AGG}, score = NLL наступного syscall'а)")
    print(classification_report(truth, predicted_attack, target_names=["Normal", "Attack"], digits=3, zero_division=0))
    if len(set(truth)) == 2:
        auc = roc_auc_score(truth, window_scores)
        print(f"Площа під ROC-кривою (ROC-AUC): {auc:.4f}")
        plot_roc_curve(truth, window_scores, service_name, auc, roc_tags)
    else:
        print("У test-спліті присутній тільки один клас вікон — ROC-AUC не рахується")


def calibrate_and_evaluate(
    service_name: str,
    model: SyscallLSTM,
    val_loader: DataLoader,
    test_loader: DataLoader | None,
    device: torch.device,
    roc_tags: tuple[str, ...],
    epoch_label: str | None = None,
) -> float:
    threshold = calibrate_threshold(model, val_loader, device)
    prefix = f"[{service_name}]" + (f" ({epoch_label})" if epoch_label else "")
    print(f"{prefix} поріг тривоги (nll, {config.THRESHOLD_PERCENTILE}-й перцентиль val): {threshold:.4f}")
    if test_loader is not None:
        print(f"{prefix} diagnostics-оцінка на test-спліті:")
        quick_test_evaluation(model, test_loader, threshold, device, service_name, roc_tags)
    return threshold
