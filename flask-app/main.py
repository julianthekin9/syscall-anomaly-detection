from normal_traffic import run_normal_traffic
from abnormal_traffic import run_abnormal_traffic


import threading
import subprocess
import time
import os


def start_flask_app():
    try:
        print(
            "Starting Flask app...",
            flush=True
        )

        subprocess.Popen(["docker", "compose", "up", "-d"])
    except Exception as e:
        print(f"Error starting Flask app: {e}", flush=True)


def normal(session_count: int):
    for _ in range(session_count):
        threading.Thread(target=run_normal_traffic).start()

def normal_and_abnormal():

    normal_thread = threading.Thread(target=run_normal_traffic)
    abnormal_thread = threading.Thread(target=run_abnormal_traffic)

    normal_thread.start()
    abnormal_thread.start()

