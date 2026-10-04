import gc
import logging

import torch

import syscall_hids
from syscall_hids.data.layout import list_services
from syscall_hids.tools import resource_guard
from syscall_hids.tools.arg_parser import build_default_arg_parser
from syscall_hids.tools.arg_parser_tools import check_args
from syscall_hids.tools.train import train_one_service
from syscall_hids.tools.utils import get_git_commit, get_tag, set_seeds, setup_logger


def main() -> None:
    parser = build_default_arg_parser()
    args = parser.parse_args()
    run(args)


def run(args) -> None:
    tag = get_tag(name=args.name, seed=args.seed)
    args, input_log_messages = check_args(args)
    set_seeds(args.seed)
    setup_logger(level=args.log_level, tag=tag, directory=args.log_dir, append=args.restart_latest)
    logging.info("===========VERIFYING SETTINGS===========")
    for message, loglevel in input_log_messages:
        logging.log(level=loglevel, msg=message)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logging.info(f"syscall_hids version: {syscall_hids.__version__}")
    logging.info(f"Пристрій: {device}")
    logging.debug(f"Configuration: {vars(args)}")
    git_commit = get_git_commit()
    logging.debug(f"Current Git commit: {git_commit}")

    resource_guard.configure(
        args.ram_guard_enabled, args.ram_soft_limit_percent, args.ram_hard_limit_percent, args.ram_throttle_sleep_sec
    )

    services = list_services(args.dataset_root, args.services)
    logging.info(f"Сервіси: {services}")

    for service_name in services:
        train_one_service(service_name, device, args, git_commit=git_commit)
        gc.collect()
        resource_guard.check_ram(f"після сервісу {service_name}")


if __name__ == "__main__":
    main()
