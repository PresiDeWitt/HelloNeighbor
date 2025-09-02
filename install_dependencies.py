#!/usr/bin/env python3
import subprocess
import sys


def install_dependencies():
    requirements = [
        "pyautogui", "opencv-python", "pillow", "cryptography",
        "termcolor", "psutil", "pyfiglet", "tabulate", "netifaces",
        "wmi", "pywin32", "pycryptodome", "requests"
    ]

    for package in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} instalado")
        except Exception as e:
            print(f"❌ Error instalando {package}: {e}")


if __name__ == "__main__":
    install_dependencies()