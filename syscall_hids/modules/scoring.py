import torch
import torch.nn.functional as F

def compute_step_scores(logits_syscall: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
    target_syscall = targets[..., 0]
    log_probs = F.log_softmax(logits_syscall, dim=-1)  # [batch, seq, vocab]
    target_log_probs = log_probs.gather(-1, target_syscall.unsqueeze(-1)).squeeze(-1)  # [batch, seq]
    return -target_log_probs


def aggregate_window_scores(step_scores: torch.Tensor, window_agg: str = "max", window_agg_quantile: float = 0.9) -> torch.Tensor:
    if window_agg == "max":
        return step_scores.max(dim=1).values  # [batch]
    elif window_agg == "quantile":
        return step_scores.quantile(window_agg_quantile, dim=1)  # [batch]
    elif window_agg == "mean":
        return step_scores.mean(dim=1)  # [batch]
    else:
        raise ValueError(f"Unknown window_agg={window_agg!r}; expected 'max', 'quantile', or 'mean'")


def compute_window_scores(
    logits_syscall: torch.Tensor,
    targets: torch.Tensor,
    window_agg: str = "max",
    window_agg_quantile: float = 0.9,
) -> torch.Tensor:
    step_scores = compute_step_scores(logits_syscall, targets)
    return aggregate_window_scores(step_scores, window_agg=window_agg, window_agg_quantile=window_agg_quantile)
