#!/usr/bin/env python3
from cryptography.fernet import Fernet
import base64

print("🔑 Generador de Claves Fernet Válidas")
print("=" * 40)

# Método 1: Generar automáticamente
auto_key = Fernet.generate_key()
print("✅ Clave generada automáticamente:")
print(f"Clave: {auto_key.decode()}")
print(f"Longitud: {len(auto_key)} bytes")
print(f"Caracteres: {len(auto_key.decode())}")

# Método 2: Crear manualmente (32 bytes)
print("\n✅ Clave manual válida:")
manual_key = base64.urlsafe_b64encode(b'x' * 32)  # 32 bytes exactos
print(f"Clave: {manual_key.decode()}")
print(f"Longitud: {len(manual_key)} bytes")

# Verificar
try:
    cipher = Fernet(manual_key)
    print("🎯 Clave verificada: VÁLIDA")
except Exception as e:
    print(f"❌ Clave inválida: {e}")

print("\n📋 Para usar en tu código:")
print(f'self.encryption_key = b"{manual_key.decode()}"')
