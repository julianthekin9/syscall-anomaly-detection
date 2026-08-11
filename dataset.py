"""torch Dataset для авторегрессионных последовательностей next-syscall
prediction. Все последовательности фиксированной длины (config.SEQ_LEN) —
паддинг не нужен, поэтому используется стандартный DataLoader без
кастомного collate_fn.

X/y хранятся как numpy-массивы (int32/int64), а не как списки Python-
объектов — на больших датасетах это заметно снижает пиковое потребление
памяти (см. data.py: make_sequences/build_normal_sequences/build_test_sequences).
torch.from_numpy() не копирует данные, только оборачивает существующий
буфер памяти в тензор — конвертация в тензор на каждый __getitem__ дешёвая.
"""

import numpy as np
import torch
from torch.utils.data import Dataset


class SequenceDataset(Dataset):
    """X[i]: [seq_len, num_features] — вход. y[i]: [seq_len] — id следующего
    syscall'а на каждом шаге (next-token target)."""

    def __init__(self, X, y) -> None:
        self.X = np.asarray(X)
        self.y = np.asarray(y)
        if len(self.X) != len(self.y):
            raise ValueError(f"X и y разной длины: {len(self.X)} vs {len(self.y)}")

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        x = torch.from_numpy(self.X[idx]).long()
        y = torch.from_numpy(self.y[idx]).long()
        return x, y


class EvalSequenceDataset(Dataset):
    """То же самое + метка окна (атака/норма) — для diagnostics-оценки на
    test-сплите в predict.py. Метка НЕ участвует в forward-проходе модели,
    только возвращается рядом для последующего сравнения с anomaly score."""

    def __init__(self, X, y, window_is_attack) -> None:
        self.X = np.asarray(X)
        self.y = np.asarray(y)
        self.window_is_attack = np.asarray(window_is_attack, dtype=bool)
        if not (len(self.X) == len(self.y) == len(self.window_is_attack)):
            raise ValueError("X, y и window_is_attack должны быть одной длины")

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, bool]:
        x = torch.from_numpy(self.X[idx]).long()
        y = torch.from_numpy(self.y[idx]).long()
        return x, y, bool(self.window_is_attack[idx])
