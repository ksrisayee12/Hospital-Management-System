"""
Encryption utilities using AES-256 (Fernet).
"""
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from app.utils.exceptions import EncryptionError


class EncryptionService:
    """Handle AES-256 encryption for sensitive data."""
    
    @staticmethod
    def _derive_key(master_key: str, salt: bytes) -> bytes:
        """Derive encryption key from master key."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 32 bytes for AES-256
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(master_key.encode())
        return base64.urlsafe_b64encode(key)
    
    @staticmethod
    def encrypt(data: str, encryption_key: str) -> str:
        """Encrypt data using AES-256."""
        try:
            # Generate random salt
            import os
            salt = os.urandom(16)
            
            # Derive key
            key = EncryptionService._derive_key(encryption_key, salt)
            
            # Encrypt
            cipher = Fernet(key)
            encrypted = cipher.encrypt(data.encode())
            
            # Return salt + encrypted data (base64)
            return base64.b64encode(salt + encrypted).decode()
        
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {str(e)}")
    
    @staticmethod
    def decrypt(encrypted_data: str, encryption_key: str) -> str:
        """Decrypt AES-256 encrypted data."""
        try:
            # Decode from base64
            decoded = base64.b64decode(encrypted_data.encode())
            
            # Extract salt (first 16 bytes) and encrypted data
            salt = decoded[:16]
            encrypted = decoded[16:]
            
            # Derive key with same salt
            key = EncryptionService._derive_key(encryption_key, salt)
            
            # Decrypt
            cipher = Fernet(key)
            decrypted = cipher.decrypt(encrypted).decode()
            
            return decrypted
        
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {str(e)}")
