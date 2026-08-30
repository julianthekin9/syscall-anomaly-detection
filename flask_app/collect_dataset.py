from pathlib import Path

from scenarios import TrafficRunner, normal, abnormal_command_execution, abnormal_network, abnormal_process_info
from utils.ebpf import EbpfSession
from utils.sudo import get_real_uid_gid, chown_recursive

CONTAINER = 'flask-app'

BASE_DIR = Path('..') / 'DATASET' / 'FLASK' 
TRAINING_DIR = BASE_DIR / 'training'
VAL_DIR = BASE_DIR / 'validation'
TEST_DIR = BASE_DIR / 'test'

NORMAL_TEST_DIR = TEST_DIR / 'normal'
ABNORMAL_TEST_DIR = TEST_DIR / 'abnormal'
MIXED_TEST_DIR = TEST_DIR / 'mixed'

NORMAL_PREFIX = 'normal'
ABNORMAL_PREFIX = 'abnormal'
MIXED_PREFIX = 'mixed'

INSTANCE_COUNTS = range(1, 10)

TOTAL_SESSION_SECONDS = 180
MIN_DURATION = 15 

def collect_normal(session: EbpfSession, output_dir: Path, prefix: str, id_range: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for idx in range(id_range):
        for instance_count in INSTANCE_COUNTS:
            duration = max(MIN_DURATION, TOTAL_SESSION_SECONDS / instance_count)
            output_path = output_dir / f"{prefix}_{idx:03d}_{instance_count}.sc"
            with session.collect_to(str(output_path)):
                TrafficRunner([normal(duration=duration, instance_count=instance_count)]).run()

def collect_abnormal(session: EbpfSession, output_dir: Path, prefix: str, id_range: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)  
    for idx in range(id_range):
        output_path = output_dir / f"{prefix}_{idx:03d}.sc" 
        with session.collect_to(str(output_path)):
            TrafficRunner([
                abnormal_command_execution(duration=50),
                abnormal_network(duration=50),
                abnormal_process_info(duration=50),
            ]).run()


def collect_mixed(session: EbpfSession, output_dir: Path, prefix: str, id_range: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for idx in range(id_range):
        output_path = output_dir / f"{prefix}_{idx:03d}.sc"
        with session.collect_to(str(output_path)):
            TrafficRunner([
                normal(duration=25, instance_count=3),
                abnormal_command_execution(duration=25, instance_count=2),
                abnormal_network(duration=25, instance_count=2),
                abnormal_process_info(duration=25, instance_count=2),
            ]).run()


def collect_training(session: EbpfSession) -> None:
    collect_normal(session, TRAINING_DIR, NORMAL_PREFIX, id_range=3)


def collect_validation(session: EbpfSession) -> None:
    collect_normal(session, VAL_DIR, NORMAL_PREFIX, id_range=2)


def collect_test(session: EbpfSession) -> None:
    # collect_abnormal(session, ABNORMAL_TEST_DIR, ABNORMAL_PREFIX, id_range=10)
    # collect_normal(session, NORMAL_TEST_DIR, NORMAL_PREFIX, id_range=1)
    collect_mixed(session, MIXED_TEST_DIR, MIXED_PREFIX, id_range=10)


if __name__ == '__main__':
    session = EbpfSession(container=CONTAINER)
    try:
        # collect_training(session)
        # collect_validation(session)
        collect_test(session)
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
 
