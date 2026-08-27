from pathlib import Path

from scenarios import TrafficRunner, normal, abnormal_command_execution, abnormal_network, abnormal_process_info
from ebpf import EbpfSession
from sudo_utils import get_real_uid_gid, chown_recursive

CONTAINER = 'flask-app'

BASE_DIR = Path('..') / 'REAL' 
MIXED_TEST_DIR = BASE_DIR / 'mixed'

MIXED_PREFIX = 'mixed'

INSTANCE_COUNTS = range(1, 10)

TOTAL_SESSION_SECONDS = 180
MIN_DURATION = 15 

def _collect_mixed(session: EbpfSession, output_dir: Path, prefix: str, id_range: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for idx in range(id_range):
        output_path = output_dir / f"{prefix}_{idx:03d}.sc"
        with session.collect_to(str(output_path)):
            timestamps = TrafficRunner([
                normal(duration=50, instance_count=3, delay=0),
                abnormal_command_execution(duration=30, delay=20),
                abnormal_network(duration=30, delay=20),
                abnormal_process_info(duration=30, delay=20),
            ]).run()

            print(timestamps)


def collect_mixed(session: EbpfSession) -> None:
    pass


if __name__ == '__main__':
    session = EbpfSession(container=CONTAINER)
    try:
        _collect_mixed(session, MIXED_TEST_DIR, MIXED_PREFIX, 1)
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
 
