from normal_traffic import run_normal_traffic
from abnormal_traffic import run_abnormal_traffic


import threading
import subprocess
import time
import os


def main():
    subprocess.Popen(["docker", "compose", "up", "-d"])
    