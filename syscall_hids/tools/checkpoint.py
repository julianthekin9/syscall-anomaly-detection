import os

import torch

from syscall_hids import config
from syscall_hids.modules.models import SyscallLSTM

def load_model(service_name: str, device: torch.device) -> tuple[SyscallLSTM, dict]:
    path = os.path.join(config.MODEL_DIR, f"{service_name}.pt")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Checkpoint {path} not found — train the model first: hids-train --service {service_name}")

    checkpoint = torch.load(path, map_location=device)
    model = SyscallLSTM.from_checkpoint(checkpoint, device)
    model.eval()
    return model, checkpoint
