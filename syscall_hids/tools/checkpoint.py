import os

import torch

from syscall_hids.modules.models import SyscallLSTM

def load_model(service_name: str, device: torch.device, model_dir: str) -> tuple[SyscallLSTM, dict]:
    path = os.path.join(model_dir, f"{service_name}.pt")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Checkpoint {path} not found — train the model first: hids-train --services {service_name}")

    checkpoint = torch.load(path, map_location=device)
    model = SyscallLSTM.from_checkpoint(checkpoint, device)
    model.eval()
    return model, checkpoint


def checkpoint_features(checkpoint: dict) -> tuple[list[str], int]:
    """(features, arg_count_buckets), з якими навчена модель: кодування має їм відповідати."""
    return list(checkpoint["hparams"]["features"]), checkpoint["vocab_sizes"].get("arg_count", 0)
