"""LSTM для предсказания следующего syscall'а И следующего процесса по
предыдущим N шагам (next-token prediction, multi-task), плюс функции
подсчёта anomaly score по выходу модели.

Архитектура: отдельный Embedding на каждый категориальный признак (syscall,
process, direction, опционально arg_count-bucket) — конкатенация — LSTM —
ДВА линейных слоя ("головы"), каждый проецирует скрытое состояние КАЖДОГО
шага в логиты по своему словарю: syscall и process.

ЗАЧЕМ ВТОРАЯ ГОЛОВА (process): часть атак (типично — web-shell/RCE через
уязвимость приложения) не создаёт необычной последовательности syscall'ов —
запрос обрабатывается штатным кодом, вызовы самые обычные (read/write/
execve). Зато процесс, который эти вызовы делает, может быть аномалией:
веб-сервер (httpd/java) внезапно порождает shell или другой процесс,
которого не было в train. Раньше process участвовал только как ВХОД
(эмбеддинг) — модель не пыталась его предсказывать и "удивляться". Теперь
anomaly score — это syscall_score + PROCESS_SCORE_WEIGHT * process_score
(см. config.py), то есть ловит оба типа сигнала.
"""

from dataclasses import asdict, dataclass

import torch
import torch.nn.functional as F
from torch import nn

import config
from data import FEATURE_NAMES

# Версия архитектуры — меняйте при любом изменении структуры state_dict
# (новые/переименованные слои, другой набор голов и т.п.). Чекпоинты со
# старой/отсутствующей версией отбраковываются ЯВНО (понятная ошибка), а не
# падают с непонятным RuntimeError из load_state_dict при mismatch'е ключей.
ARCHITECTURE_VERSION = 2  # v1 = одна голова (только syscall), v2 = +process-голова


@dataclass(frozen=True)
class ModelHParams:
    """Всё, что нужно, чтобы однозначно восстановить архитектуру SyscallLSTM
    (в отличие от seq_len/score_method/threshold — это НЕ гиперпараметры
    архитектуры, а про данные/детекцию, поэтому их здесь нет).

    Ключевая причина существования этого класса: раньше SyscallLSTM.__init__
    читал эти значения напрямую из живого config.py, а чекпоинт хранил их
    просто "на память", не как источник истины. Если между обучением и
    инференсом (или между двумя RESUME-запусками) поменять, например,
    config.HIDDEN_DIM — модель конструировалась под НОВЫЙ config, а веса
    в чекпоинте были под СТАРЫЙ, и load_state_dict падал с ошибкой
    размерности. Теперь чекпоинт — источник истины при загрузке/дообучении,
    config.py используется только при обучении "с нуля".
    """

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
        if "hparams" in checkpoint:
            return cls(**checkpoint["hparams"])
        # Обратная совместимость со старыми чекпоинтами (сохранены плоско,
        # без единого ключа "hparams") — поля называются так же.
        return cls(
            embed_dim_syscall=checkpoint["embed_dim_syscall"],
            embed_dim_process=checkpoint["embed_dim_process"],
            embed_dim_direction=checkpoint["embed_dim_direction"],
            embed_dim_arg_count=checkpoint["embed_dim_arg_count"],
            use_arg_count_feature=checkpoint["use_arg_count_feature"],
            hidden_dim=checkpoint["hidden_dim"],
            num_layers=checkpoint["num_layers"],
            dropout=checkpoint["dropout"],
        )

    def to_dict(self) -> dict:
        return asdict(self)


class CheckpointArchitectureMismatch(RuntimeError):
    """Чекпоинт сохранён другой версией архитектуры модели (см.
    ARCHITECTURE_VERSION) — веса структурно несовместимы (другой набор
    слоёв), дообучение/загрузка невозможны, нужно обучение с нуля."""


class SyscallLSTM(nn.Module):
    """vocab_sizes: {"syscall": N, "process": N, "direction": N, ["arg_count": N]}
    (ключ "arg_count" присутствует, только если hparams.use_arg_count_feature=True
    — в этом случае он должен быть последним в FEATURE_NAMES-порядке входа).

    forward() возвращает ДВА тензора логитов: (logits_syscall, logits_process).

    hparams: если не передан — берётся из текущего config.py (обучение с
    нуля). При загрузке/дообучении из чекпоинта ВСЕГДА передавайте
    ModelHParams.from_checkpoint(checkpoint) явно — не полагайтесь на
    default. Удобнее использовать SyscallLSTM.from_checkpoint(...) ниже.
    """

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
        self.output_process = nn.Linear(self.hparams.hidden_dim, vocab_sizes["process"])

    @classmethod
    def from_checkpoint(cls, checkpoint: dict, device: torch.device | str = "cpu") -> "SyscallLSTM":
        """Единая точка восстановления модели из чекпоинта: архитектура
        берётся из checkpoint (через ModelHParams), а не из живого config.py."""
        ckpt_version = checkpoint.get("architecture_version")
        if ckpt_version != ARCHITECTURE_VERSION:
            raise CheckpointArchitectureMismatch(
                f"Чекпоинт сохранён архитектурой версии {ckpt_version!r}, а текущий код — "
                f"версии {ARCHITECTURE_VERSION} (см. model.ARCHITECTURE_VERSION). Скорее всего "
                f"это старый однобашенный чекпоинт (только syscall-голова, без process). "
                f"Загрузка/дообучение невозможны — переобучите сервис с нуля: "
                f"config.RESUME=False (или удалите файл чекпоинта) и запустите train.py заново."
            )
        hparams = ModelHParams.from_checkpoint(checkpoint)
        model = cls(checkpoint["vocab_sizes"], hparams=hparams).to(device)
        model.load_state_dict(checkpoint["model_state"])
        return model

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """x: [batch, seq_len, num_features] (порядок фич — self.feature_order).
        Возвращает (logits_syscall [batch, seq_len, vocab_syscall],
                     logits_process [batch, seq_len, vocab_process])."""
        embedded = [
            self.embeddings[name](x[:, :, i]) for i, name in enumerate(self.feature_order)
        ]
        combined = torch.cat(embedded, dim=-1)  # [batch, seq_len, total_embed_dim]
        hidden_states, _ = self.lstm(combined)  # [batch, seq_len, hidden_dim]
        logits_syscall = self.output_syscall(hidden_states)
        logits_process = self.output_process(hidden_states)
        return logits_syscall, logits_process


def _single_head_step_scores(logits: torch.Tensor, targets: torch.Tensor, method: str = "nll", top_k: int = 5) -> torch.Tensor:
    """Anomaly score НА КАЖДЫЙ ШАГ для ОДНОЙ головы (без агрегации по окну)
    [batch, seq_len].

    method:
        "nll"   — -log(P(правильное значение)) на каждом шаге. Высокий score
                  = модель не верила в то, что реально произошло.
        "top_k" — 1 на шагах, где истинное значение НЕ попало в top-k
                  предсказанных моделью (классический STIDE-подход).
    """
    if method == "nll":
        log_probs = F.log_softmax(logits, dim=-1)  # [batch, seq, vocab]
        target_log_probs = log_probs.gather(-1, targets.unsqueeze(-1)).squeeze(-1)  # [batch, seq]
        return -target_log_probs
    elif method == "top_k":
        topk_indices = logits.topk(top_k, dim=-1).indices  # [batch, seq, k]
        hit = (topk_indices == targets.unsqueeze(-1)).any(dim=-1)  # [batch, seq] bool
        return (~hit).float()
    else:
        raise ValueError(f"Неизвестный method={method!r}, ожидалось 'nll' или 'top_k'")


def compute_step_scores_components(
    logits_syscall: torch.Tensor,
    logits_process: torch.Tensor,
    targets: torch.Tensor,
    method: str = "nll",
    top_k: int = 5,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Раздельные per-step score для syscall- и process-головы (НЕ взвешены,
    НЕ объединены) — [batch, seq_len] каждый.

    targets: [batch, seq_len, 2] — targets[..., 0] = syscall-таргет,
             targets[..., 1] = process-таргет (см. data.make_sequences).
    """
    syscall_scores = _single_head_step_scores(logits_syscall, targets[..., 0], method=method, top_k=top_k)
    process_scores = _single_head_step_scores(logits_process, targets[..., 1], method=method, top_k=top_k)
    return syscall_scores, process_scores


def combine_step_scores(syscall_scores: torch.Tensor, process_scores: torch.Tensor, process_weight: float = 1.0) -> torch.Tensor:
    """Итоговый per-step anomaly score = syscall_score + process_weight * process_score.
    process_weight — config.PROCESS_SCORE_WEIGHT (насколько сильно "неожиданный
    процесс" считается такой же весомой аномалией, как "неожиданный syscall")."""
    return syscall_scores + process_weight * process_scores


def aggregate_window_scores(step_scores: torch.Tensor, window_agg: str = "max", window_agg_quantile: float = 0.9) -> torch.Tensor:
    """Свёртка step_scores [batch, seq_len] в один score на окно [batch].

    "max"      — худший (самый аномальный) шаг окна. Чувствителен к атакам
                 ЛЮБОЙ длины внутри окна (даже 1 шаг), но может насыщаться,
                 если единичные-но-легитимные выбросы NLL встречаются почти
                 в каждом окне независимо от того, атака это или нет —
                 тогда разделяющая способность падает (см. AUC).
    "quantile" — window_agg_quantile-й перцентиль step_scores (нужен
                 минимум (1-quantile)-доля "плохих" шагов в окне).
    "mean"     — среднее по всем шагам окна. Менее чувствителен к единичным
                 всплескам, зато требует, чтобы аномальность была "размазана"
                 по значительной части окна, а не сосредоточена в паре шагов.
    """
    if window_agg == "max":
        return step_scores.max(dim=1).values  # [batch]
    elif window_agg == "quantile":
        return step_scores.quantile(window_agg_quantile, dim=1)  # [batch]
    elif window_agg == "mean":
        return step_scores.mean(dim=1)  # [batch]
    else:
        raise ValueError(f"Неизвестный window_agg={window_agg!r}, ожидалось 'max', 'quantile' или 'mean'")


def compute_window_scores(
    logits_syscall: torch.Tensor,
    logits_process: torch.Tensor,
    targets: torch.Tensor,
    method: str = "nll",
    top_k: int = 5,
    process_weight: float = 1.0,
    window_agg: str = "max",
    window_agg_quantile: float = 0.9,
) -> torch.Tensor:
    """compute_step_scores_components + combine_step_scores + aggregate_window_scores
    за один вызов (для случаев, когда нужен только ОДИН итоговый score —
    обучение, калибровка порога). Если нужно сравнить компоненты
    (syscall-only / process-only / комбинированный) на одних и тех же
    логитах (диагностика) — вызывайте compute_step_scores_components один
    раз и комбинируйте/агрегируйте сами, см. train.quick_test_evaluation.
    """
    syscall_scores, process_scores = compute_step_scores_components(logits_syscall, logits_process, targets, method=method, top_k=top_k)
    combined = combine_step_scores(syscall_scores, process_scores, process_weight=process_weight)
    return aggregate_window_scores(combined, window_agg=window_agg, window_agg_quantile=window_agg_quantile)
