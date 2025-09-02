#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

from cryptography.fernet import Fernet
import hashlib
import base64


def generate_encryption_key():
    """Generar clave de cifrado segura"""
    return Fernet.generate_key()


def derive_key_from_password(password, salt=None):
    """Derivar clave criptográfica de una contraseña"""
    if salt is None:
        salt = os.urandom(16)

    # Usar PBKDF2 para derivar clave
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt,
        100000,  # 100,000 iteraciones
        32  # 32 bytes = 256 bits
    )

    # Codificar para Fernet
    fernet_key = base64.urlsafe_b64encode(key)
    return fernet_key, salt


class SecureConfig:
    def __init__(self):
        self.encryption_key = None
        self.authorized_clients = set()

    def setup_encryption(self, password=None):
        """Configurar cifrado"""
        if password:
            self.encryption_key, salt = derive_key_from_password(password)
        else:
            self.encryption_key = generate_encryption_key()

        return self.encryption_key

    def add_authorized_client(self, client_ip):
        """Añadir cliente autorizado"""
        self.authorized_clients.add(client_ip)

    def is_client_authorized(self, client_ip):
        """Verificar si cliente está autorizado"""
        return client_ip in self.authorized_clients


# Ejemplo de configuración segura
if __name__ == "__main__":
    config = SecureConfig()

    # Configurar con contraseña o generar clave automática
    use_password = input("¿Usar contraseña? (s/n): ").lower() == 's'

    if use_password:
        password = input("Introduce contraseña: ")
        key = config.setup_encryption(password)
    else:
        key = config.setup_encryption()

    print(f"Clave de cifrado: {key.decode()}")

    # Añadir IPs autorizadas
    config.add_authorized_client("192.168.1.50")
    config.add_authorized_client("192.168.1.100")

    print("Configuración de seguridad completada")