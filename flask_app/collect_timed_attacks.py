from pathlib import Path

from scenarios import TrafficRunner, normal, abnormal_command_execution, abnormal_network, abnormal_process_info
from ebpf import EbpfSession
from sudo_utils import get_real_uid_gid, chown_recursive

import json 

CONTAINER = 'flask-app'

BASE_DIR = Path('..') / 'REAL' 
MIXED_TEST_DIR = BASE_DIR / 'mixed'

MIXED_PREFIX = 'mixed'

INFO_PATH = MIXED_TEST_DIR / 'info.json'

INSTANCE_COUNTS = range(1, 10)

TOTAL_SESSION_SECONDS = 180
MIN_DURATION = 15 

def _collect_mixed(session: EbpfSession, output_path: str) -> float:
    with session.collect_to(str(output_path)):
        timestamps = TrafficRunner([
            normal(duration=30, instance_count=2, delay=0),
            abnormal_command_execution(duration=28, delay=2),
            abnormal_network(duration=28, delay=2),
            abnormal_process_info(duration=28, delay=2),
        ]).run()

        return timestamps["abnormal:command_execution"]


def collect_mixed(session: EbpfSession, id_range: int) -> None:
    output_dir = MIXED_TEST_DIR
    prefix = MIXED_PREFIX
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamps : dict[str, float] = {}

    for idx in range(id_range):
        filename = f"{prefix}_{idx:03d}.sc"
        output_path = output_dir / filename
        timestamp = _collect_mixed(session, output_path)
        timestamps[filename] = timestamp

    return timestamps
        

if __name__ == '__main__':
    session = EbpfSession(container=CONTAINER)
    try:
       timestamps  = collect_mixed(session, 2)

       with open(INFO_PATH, "w") as f:
        json.dump(timestamps, f)

    #    print(timestamps)
    finally:
        session.close()

        real_owner = get_real_uid_gid()

        if real_owner is not None:
            chown_recursive(BASE_DIR, *real_owner)
        else:
            print(
                "SUDO_UID/SUDO_GID не найдены — владелец файлов не изменён "
                "(скрипт запущен не через sudo?)"
            )
 
