import requests
import random
import time


BASE_URL = "http://localhost:5000"


def request(method, endpoint, **kwargs):
    try:
        response = requests.request(
            method,
            BASE_URL + endpoint,
            timeout=3,
            **kwargs
        )
        print(
            f"{method:6} "
            f"{endpoint:45} "
            f"{response.status_code}",
            flush=True
        )
        return response
    except Exception as e:
        print(f"ERROR {method} {endpoint}: {e}", flush=True)
        return None


def _command_execution_once():
    commands = [
        "id", "whoami", "pwd", "ls", "ls -la",
        "ps", "uname", "hostname", "mount"
    ]
    command = random.choice(commands)
    request("GET", "/api/debug/run", json={"command": command})
    time.sleep(random.uniform(0.1, 0.5))


def _process_info_once():
    request("GET", "/api/debug/process-info")
    time.sleep(random.uniform(0.1, 0.5))


def _network_once():
    request("GET", "/api/debug/network")
    time.sleep(random.uniform(0.1, 0.5))


def _run_for(fn, duration: float) -> None:
    deadline = time.time() + duration
    while time.time() < deadline:
        fn()


def command_execution(duration: float) -> None:
    _run_for(_command_execution_once, duration)


def process_info(duration: float) -> None:
    _run_for(_process_info_once, duration)


def network(duration: float) -> None:
    _run_for(_network_once, duration)