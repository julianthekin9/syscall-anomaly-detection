from dataclasses import asdict, dataclass

import torch
from torch import nn

ARCHITECTURE_VERSION = 3


@dataclass(frozen=True)
class ModelHParams:
    embed_dim_syscall: int
    embed_dim_process: int
    embed_dim_direction: int
    embed_dim_arg_count: int
    features: tuple[str, ...]  # вибрані вхідні ознаки в канонічному порядку (data.vocab.FEATURE_NAMES)
    hidden_dim: int
    num_layers: int
    dropout: float

    @classmethod
    def from_args(cls, args) -> "ModelHParams":
        return cls(
            embed_dim_syscall=args.embed_dim_syscall,
            embed_dim_process=args.embed_dim_process,
            embed_dim_direction=args.embed_dim_direction,
            embed_dim_arg_count=args.embed_dim_arg_count,
            features=tuple(args.features),
            hidden_dim=args.hidden_dim,
            num_layers=args.num_layers,
            dropout=args.dropout,
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
    def __init__(self, vocab_sizes: dict[str, int], hparams: ModelHParams) -> None:
        super().__init__()

        self.hparams = hparams

        self.feature_order = list(self.hparams.features)

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
        """x: [batch, seq_len, num_features] (feature order: self.feature_order).
        Returns logits_syscall [batch, seq_len, vocab_syscall]."""
        embedded = [
            self.embeddings[name](x[:, :, i]) for i, name in enumerate(self.feature_order)
        ]
        combined = torch.cat(embedded, dim=-1)  # [batch, seq_len, total_embed_dim]
        hidden_states, _ = self.lstm(combined)  # [batch, seq_len, hidden_dim]
        logits_syscall = self.output_syscall(hidden_states)
        return logits_syscall
