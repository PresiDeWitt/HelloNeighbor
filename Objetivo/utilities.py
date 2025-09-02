import os
import json
import socket
import platform
import psutil
from datetime import datetime
from termcolor import colored


def log_action(action: str, target: str = None, details: str = None, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    color = {
        "INFO": 'green',
        "WARN": 'yellow',
        "CRIT": 'red',
        "DEBUG": 'blue'
    }.get(level, 'white')

    if target:
        msg = colored(f"[{timestamp}] [{level}] {action} on {target}", color)
    else:
        msg = colored(f"[{timestamp}] [{level}] {action}", color)

    if details:
        msg += colored(f"\n    |_ Details: {details}", 'cyan')

    print(msg)

    # Ruta de logs en carpeta TEMP de Windows
    temp_dir = os.environ.get('TEMP', os.getcwd())
    log_path = os.path.join(temp_dir, "systemdiag.log")

    with open(log_path, 'a', encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{level}] {action}\n")


def get_system_info():
    return {
        'hostname': socket.gethostname(),
        'user': os.getenv('USERNAME'),
        'os': platform.platform(),
        'processors': psutil.cpu_count(),
        'memory': psutil.virtual_memory().total,
        'disks': [d.device for d in psutil.disk_partitions()]
    }


def secure_delete(file_path: str, passes=7):
    try:
        with open(file_path, 'ba+') as f:
            length = f.tell()
            for _ in range(passes):
                f.seek(0)
                f.write(os.urandom(length))
        os.remove(file_path)
        log_action(f"Securely deleted {file_path}", level="DEBUG")
    except Exception as e:
        log_action(f"Failed to securely delete {file_path}", details=str(e), level="WARN")
