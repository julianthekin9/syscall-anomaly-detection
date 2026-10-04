from dataclasses import asdict, dataclass

import torch
import torch.nn.functional as F
from torch import nn

import config
from data import FEATURE_NAMES


ARCHITECTURE_VERSION = 3


@dataclass(frozen=True)
class ModelHParams:
    embed_dim_syscall: int
    embed_dim_process: int
    embed_dim_direction: int
    embed_dim_arg_count: int
    use_arg_count_feature: bool
    hidden_dim: int
    num_layers: int
    dropout: float

    @classmethod
    def from_config(cls) -> "ModelHParams":
        return cls(
            embed_dim_syscall=config.EMBED_DIM_SYSCALL,
            embed_dim_process=config.EMBED_DIM_PROCESS,
            embed_dim_direction=config.EMBED_DIM_DIRECTION,
            embed_dim_arg_count=config.EMBED_DIM_ARG_COUNT,
            use_arg_count_feature=config.USE_ARG_COUNT_FEATURE,
            hidden_dim=config.HIDDEN_DIM,
            num_layers=config.NUM_LAYERS,
            dropout=config.DROPOUT,
        )

    @classmethod
    def from_checkpoint(cls, checkpoint: dict) -> "ModelHParams":
        return cls(**checkpoint["hparams"])

    def to_dict(self) -> dict:
        return asdict(self)


class CheckpointArchitectureMismatch(RuntimeError):
    """The checkpoint was saved with a different model architecture version (see
    ARCHITECTURE_VERSION) — the weights are structurally incompatible (different
    set of layers), so resuming/loading is impossible; training from scratch is required."""


class SyscallLSTM(nn.Module):
    def __init__(self, vocab_sizes: dict[str, int], hparams: ModelHParams | None = None) -> None:
        super().__init__()

        self.hparams = hparams if hparams is not None else ModelHParams.from_config()

        self.feature_order = list(FEATURE_NAMES)  # ["syscall", "process", "direction"]
        if self.hparams.use_arg_count_feature:
            self.feature_order.append("arg_count")

        embed_dims = {
            "syscall": self.hparams.embed_dim_syscall,
            "process": self.hparams.embed_dim_process,
            "direction": self.hparams.embed_dim_direction,
            "arg_count": self.hparams.embed_dim_arg_count,
        }

        self.embeddings = nn.ModuleDict()
        for name in self.feature_order:
            emb = nn.Embedding(vocab_sizes[name], embed_dims[name], padding_idx=0)
            self.embeddings[name] = emb

        total_embed_dim = sum(embed_dims[name] for name in self.feature_order)

        self.lstm = nn.LSTM(
            input_size=total_embed_dim,
            hidden_size=self.hparams.hidden_dim,
            num_layers=self.hparams.num_layers,
            batch_first=True,
            dropout=self.hparams.dropout if self.hparams.num_layers > 1 else 0.0,
        )
        self.output_syscall = nn.Linear(self.hparams.hidden_dim, vocab_sizes["syscall"])

    @classmethod
    def from_checkpoint(cls, checkpoint: dict, device: torch.device | str = "cpu") -> "SyscallLSTM":
        ckpt_version = checkpoint["architecture_version"]
        if ckpt_version != ARCHITECTURE_VERSION:
            raise CheckpointArchitectureMismatch(
                f"Checkpoint was saved with architecture version {ckpt_version!r}, while the current code uses "
                f"version {ARCHITECTURE_VERSION} (see model.ARCHITECTURE_VERSION)."
            )
        hparams = ModelHParams.from_checkpoint(checkpoint)
        model = cls(checkpoint["vocab_sizes"], hparams=hparams).to(device)
        model.load_state_dict(checkpoint["model_state"])
        return model

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: [batch, seq_len, num_features] (порядок фич — self.feature_order).
        Возвращает logits_syscall [batch, seq_len, vocab_syscall]."""
        embedded = [
            self.embeddings[name](x[:, :, i]) for i, name in enumerate(self.feature_order)
        ]
        combined = torch.cat(embedded, dim=-1)  # [batch, seq_len, total_embed_dim]
        hidden_states, _ = self.lstm(combined)  # [batch, seq_len, hidden_dim]
        logits_syscall = self.output_syscall(hidden_states)
        return logits_syscall


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