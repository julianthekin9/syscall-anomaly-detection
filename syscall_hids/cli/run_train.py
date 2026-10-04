import argparse
import gc

import torch

from syscall_hids.data.layout import list_services
from syscall_hids.tools import resource_guard
from syscall_hids.tools.train import train_one_service

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--service", help="Навчити тільки один сервіс (за замовчуванням — усі з config.DATASET_ROOT)")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    services = [args.service] if args.service else list_services()
    print(f"Пристрій: {device}")
    print(f"Сервіси: {services}")

    for service_name in services:
        train_one_service(service_name, device)
        gc.collect()
        resource_guard.check_ram(f"після сервісу {service_name}")


if __name__ == "__main__":
    main()
