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


def checkpoint_features(checkpoint: dict) -> tuple[bool, int]:
    """(use_arg_count_feature, arg_count_buckets) the model was trained with: encoding must match them."""
    return checkpoint["hparams"]["use_arg_count_feature"], checkpoint["vocab_sizes"].get("arg_count", 0)
