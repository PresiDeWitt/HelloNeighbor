#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import json
import threading
import time
import subprocess
import pyautogui
import struct

from cryptography.fernet import Fernet


class SecureRemoteControlServer:
    def __init__(self, host='0.0.0.0', port=5556, encryption_key=None):
        self.host = host
        self.port = port
        self.running = False
        self.control_socket = None
        self.encryption_key = encryption_key
        self.cipher = Fernet(encryption_key) if encryption_key else None

    def encrypt_data(self, data):
        """Cifrar datos si hay clave configurada"""
        if self.cipher and isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data) if self.cipher else data

    def decrypt_data(self, encrypted_data):
        """Descifrar datos"""
        if self.cipher:
            return self.cipher.decrypt(encrypted_data).decode()
        return encrypted_data.decode()

    def execute_remote_command(self, command_type, data):
        """Ejecutar comando de control remoto REAL"""
        try:
            if command_type == 'keyboard':
                # Simular teclado
                pyautogui.write(data['text'])
                return True

            elif command_type == 'mouse':
                # Controlar mouse
                action = data['action']
                if action == 'move':
                    pyautogui.moveTo(data['x'], data['y'])
                elif action == 'click':
                    pyautogui.click(data['x'], data['y'])
                elif action == 'scroll':
                    pyautogui.scroll(data['clicks'])
                return True

            elif command_type == 'system':
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

            elif command_type == 'file':
                # Operaciones con archivos
                action = data['action']
                if action == 'list_dir':
                    import os
                    files = os.listdir(data['path'])
                    return {'success': True, 'files': files}

            return {'success': False, 'error': 'Comando desconocido'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def handle_client(self, client_socket, address):
        """Manejar cliente de forma segura"""
        print(f"🔗 Conexión de control desde {address}")

        try:
            while self.running:
                # Recibir tamaño del mensaje
                size_data = client_socket.recv(4)
                if not size_data:
                    break

                size = struct.unpack('!I', size_data)[0]
                encrypted_data = client_socket.recv(size)

                # Descifrar comando
                decrypted_data = self.decrypt_data(encrypted_data)
                command = json.loads(decrypted_data)

                # Ejecutar comando
                result = self.execute_remote_command(
                    command['type'],
                    command['data']
                )

                # Enviar respuesta cifrada
                response_json = json.dumps(result)
                encrypted_response = self.encrypt_data(response_json)

                client_socket.sendall(struct.pack('!I', len(encrypted_response)))
                client_socket.sendall(encrypted_response)

        except Exception as e:
            print(f"❌ Error con cliente {address}: {e}")
        finally:
            client_socket.close()

    def start_control_server(self):
        """Iniciar servidor de control remoto seguro"""
        self.running = True
        self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.control_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.control_socket.bind((self.host, self.port))
            self.control_socket.listen(5)
            print(f"🖥️ Servidor de control seguro iniciado en {self.host}:{self.port}")

            while self.running:
                client_socket, address = self.control_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()

        except Exception as e:
            print(f"❌ Error en servidor de control: {e}")
        finally:
            self.stop_server()

    def stop_server(self):
        """Detener servidor"""
        self.running = False
        if self.control_socket:
            self.control_socket.close()


class SecureRemoteControlClient:
    def __init__(self, target_host, port=5556, encryption_key=None):
        self.target_host = target_host
        self.port = port
        self.socket = None
        self.encryption_key = encryption_key
        self.cipher = Fernet(encryption_key) if encryption_key else None

    def encrypt_data(self, data):
        """Cifrar datos"""
        if self.cipher and isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data) if self.cipher else data

    def decrypt_data(self, encrypted_data):
        """Descifrar datos"""
        if self.cipher:
            return self.cipher.decrypt(encrypted_data).decode()
        return encrypted_data.decode()

    def connect(self):
        """Conectar al servidor de control seguro"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.target_host, self.port))
            print(f"✅ Conectado seguro a {self.target_host}:{self.port}")
            return True
        except Exception as e:
            print(f"❌ Error conectando: {e}")
            return False

    def send_command(self, command_type, data, wait_response=True):
        """Enviar comando de control seguro"""
        if not self.socket:
            if not self.connect():
                return None

        try:
            # Crear y cifrar comando
            command = {
                'type': command_type,
                'data': data,
                'timestamp': time.time()
            }

            encrypted_command = self.encrypt_data(json.dumps(command))

            # Enviar tamaño y datos
            self.socket.sendall(struct.pack('!I', len(encrypted_command)))
            self.socket.sendall(encrypted_command)

            if wait_response:
                return self._receive_response()
            return True

        except Exception as e:
            print(f"❌ Error enviando comando: {e}")
            return None

    def _receive_response(self):
        """Recibir respuesta segura"""
        try:
            size_data = self.socket.recv(4)
            if not size_data:
                return None

            size = struct.unpack('!I', size_data)[0]
            encrypted_response = self.socket.recv(size)

            return json.loads(self.decrypt_data(encrypted_response))

        except Exception as e:
            print(f"❌ Error recibiendo respuesta: {e}")
            return None

    def disconnect(self):
        """Desconectar"""
        if self.socket:
            self.socket.close()
            self.socket = None


# Uso mejorado
if __name__ == "__main__":
    # Generar clave de cifrado (debe ser la misma en cliente y servidor)
    encryption_key = Fernet.generate_key()

    # Configuración
    config = {
        'target_host': '192.168.1.100',
        'screen_port': 5555,
        'control_port': 5556,
        'encryption_key': encryption_key
    }

    # Ejemplo de uso
    client = SecureRemoteControlClient(
        config['target_host'],
        config['control_port'],
        config['encryption_key']
    )

    if client.connect():
        # Ejemplo: ejecutar comando
        result = client.send_command('system', {'command': 'dir'})
        print(f"Resultado: {result}")

        client.disconnect()