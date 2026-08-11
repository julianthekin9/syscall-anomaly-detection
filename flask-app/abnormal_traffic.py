import requests
import random
import sys
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

        print(
            f"ERROR {method} {endpoint}: {e}",
            flush=True
        )

        return None


def command_execution():

    commands = [
        "id",
        "whoami",
        "pwd",
        "ls",
        "ls -la",
        "ps",
        "uname",
        "hostname"
    ]

    for command in commands:

        request(
            "POST",
            "/api/debug/run",
            json={
                "command": command
            }
        )

        time.sleep(
            random.uniform(0.1, 0.5)
        )

def run_abnormal_traffic():

    print(
        "Starting continuous abnormal traffic generation...",
        flush=True
    )

    try:
        while True:
            command_execution()

    except KeyboardInterrupt:

        print(
            "\nStopping continuous abnormal traffic generation.",
            flush=True
        )


if __name__ == "__main__":
    run_abnormal_traffic()