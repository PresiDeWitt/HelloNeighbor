#!/usr/bin/env python3
import ctypes
from ctypes import wintypes
import sys


class Win32CryptAlternative:
    def __init__(self):
        self.crypt32 = ctypes.windll.crypt32
        self.kernel32 = ctypes.windll.kernel32

    def CryptUnprotectData(self, encrypted_data, entropy=None, flags=0):
        """Alternative to win32crypt.CryptUnprotectData"""

        class DATA_BLOB(ctypes.Structure):
            _fields_ = [('cbData', wintypes.DWORD),
                        ('pbData', ctypes.POINTER(ctypes.c_byte))]

        # Create input blob
        encrypted_bytes = bytes(encrypted_data)
        input_blob = DATA_BLOB()
        input_blob.cbData = len(encrypted_bytes)
        input_blob.pbData = ctypes.cast(ctypes.create_string_buffer(encrypted_bytes),
                                        ctypes.POINTER(ctypes.c_byte))

        # Optional entropy blob
        entropy_blob = DATA_BLOB()
        if entropy:
            entropy_bytes = bytes(entropy)
            entropy_blob.cbData = len(entropy_bytes)
            entropy_blob.pbData = ctypes.cast(ctypes.create_string_buffer(entropy_bytes),
                                              ctypes.POINTER(ctypes.c_byte))
            p_entropy = ctypes.byref(entropy_blob)
        else:
            p_entropy = None

        # Output blob
        output_blob = DATA_BLOB()

        # Call CryptUnprotectData
        success = self.crypt32.CryptUnprotectData(
            ctypes.byref(input_blob),
            None,
            p_entropy,
            None,
            None,
            flags,
            ctypes.byref(output_blob)
        )

        if not success:
            raise RuntimeError("CryptUnprotectData failed")

        try:
            # Extract decrypted data
            decrypted_data = ctypes.string_at(output_blob.pbData, output_blob.cbData)
            return decrypted_data
        finally:
            # Free memory
            self.kernel32.LocalFree(output_blob.pbData)


# Monkey patch para reemplazar win32crypt
try:
    import win32crypt

    print("✅ win32crypt encontrado, usando versión original")
except ImportError:
    print("⚠️  win32crypt no encontrado, usando alternativa")

    # Crear módulo simulado
    import sys
    from types import ModuleType

    win32crypt_module = ModuleType('win32crypt')


    def CryptUnprotectData(encrypted_data, entropy=None, flags=0):
        crypt = Win32CryptAlternative()
        return crypt.CryptUnprotectData(encrypted_data, entropy, flags)


    win32crypt_module.CryptUnprotectData = CryptUnprotectData
    sys.modules['win32crypt'] = win32crypt_module