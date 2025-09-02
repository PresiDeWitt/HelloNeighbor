import base64
import hashlib
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import hmac

class SecureComs:
    def __init__(self):
        self.session_key = get_random_bytes(32)
        self.hmac_key = get_random_bytes(32)
        self.rsa_key = self._generate_rsa_keys()
    
    def _generate_rsa_keys(self):
        key = RSA.generate(4096)
        return {
            'private': key.export_key(),
            'public': key.publickey().export_key()
        }
    
    def encrypt(self, data: str, use_rsa: bool = False) -> str:
        # Capa AES
        iv = get_random_bytes(16)
        cipher = AES.new(self.session_key, AES.MODE_CBC, iv)
        padded = pad(data.encode(), AES.block_size)
        encrypted = cipher.encrypt(padded)
        
        if use_rsa:
            # Capa RSA para la clave de sesión
            rsa_cipher = PKCS1_OAEP.new(RSA.import_key(self.rsa_key['public']))
            encrypted_key = rsa_cipher.encrypt(self.session_key)
            encrypted = base64.b64encode(encrypted_key) + b'||' + encrypted
        
        hmac_val = self._generate_hmac(iv + encrypted)
        return base64.b64encode(iv + encrypted + hmac_val).decode()
    
    def decrypt(self, enc_data: str, use_rsa: bool = False) -> str:
        raw = base64.b64decode(enc_data)
        iv, encrypted, hmac_val = raw[:16], raw[16:-32], raw[-32:]
        
        if not hmac_val == self._generate_hmac(iv + encrypted):
            raise ValueError("Invalid HMAC")
        
        if use_rsa:
            encrypted_key, encrypted = encrypted.split(b'||')
            encrypted_key = base64.b64decode(encrypted_key)
            rsa_cipher = PKCS1_OAEP.new(RSA.import_key(self.rsa_key['private']))
            self.session_key = rsa_cipher.decrypt(encrypted_key)
        
        cipher = AES.new(self.session_key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
        return decrypted.decode()
    
    def _generate_hmac(self, data: bytes) -> bytes:
        return hmac.new(self.hmac_key, data, hashlib.sha3_256).digest()