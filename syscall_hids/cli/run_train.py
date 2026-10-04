import gc

import torch

from syscall_hids.data.layout import list_services
from syscall_hids.tools import resource_guard
from syscall_hids.tools.arg_parser import build_default_arg_parser
from syscall_hids.tools.arg_parser_tools import check_args
from syscall_hids.tools.train import train_one_service


def main() -> None:
    parser = build_default_arg_parser()
    args = parser.parse_args()
    run(args)


def run(args) -> None:
    args, input_log_messages = check_args(args)
    for message in input_log_messages:
        print(f"УВАГА: {message}")
    print("Конфігурація:")
    for key, value in vars(args).items():
        print(f"  {key}: {value}")

    resource_guard.configure(
        args.ram_guard_enabled, args.ram_soft_limit_percent, args.ram_hard_limit_percent, args.ram_throttle_sleep_sec
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    services = list_services(args.dataset_root, args.services)
    print(f"Пристрій: {device}")
    print(f"Сервіси: {services}")

    for service_name in services:
        train_one_service(service_name, device, args)
        gc.collect()
        resource_guard.check_ram(f"після сервісу {service_name}")


if __name__ == "__main__":
    main()
