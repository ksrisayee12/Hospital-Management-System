import base64
import json
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Master Key (KEK) - Loaded from environment
KEK = os.getenv("MASTER_KEK", "s3cr3t_m4st3r_k3y_f0r_envel0pe_enc")
if len(KEK) < 32:
    KEK = KEK.ljust(32, "x")
KEK_BYTES = KEK[:32].encode("utf-8")

class HealthcareEncryptor:
    @staticmethod
    def encrypt(plaintext: str, key: bytes) -> dict:
        """
        Algorithm: AES-256-GCM (authenticated encryption)
        Generate a unique 96-bit nonce per encryption call
        Return: {ciphertext, nonce, tag} as base64-encoded JSON string
        """
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        
        ciphertext = ciphertext_with_tag[:-16]
        tag = ciphertext_with_tag[-16:]
        
        return {
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
            "nonce": base64.b64encode(nonce).decode('utf-8'),
            "tag": base64.b64encode(tag).decode('utf-8')
        }

    @staticmethod
    def decrypt(encrypted_data_str: str, key: bytes) -> str:
        """
        Decrypts the base64 JSON payload.
        """
        data = json.loads(encrypted_data_str)
        ciphertext = base64.b64decode(data["ciphertext"])
        nonce = base64.b64decode(data["nonce"])
        tag = base64.b64decode(data["tag"])
        
        aesgcm = AESGCM(key)
        ciphertext_with_tag = ciphertext + tag
        decrypted = aesgcm.decrypt(nonce, ciphertext_with_tag, None)
        return decrypted.decode('utf-8')

    @staticmethod
    def encrypt_bytes(raw_bytes: bytes, key: bytes) -> dict:
        """
        Encrypts raw binary data (e.g. uploaded files).
        """
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext_with_tag = aesgcm.encrypt(nonce, raw_bytes, None)
        ciphertext = ciphertext_with_tag[:-16]
        tag = ciphertext_with_tag[-16:]
        
        return {
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
            "nonce": base64.b64encode(nonce).decode('utf-8'),
            "tag": base64.b64encode(tag).decode('utf-8')
        }

    @staticmethod
    def decrypt_bytes(encrypted_data_str: str, key: bytes) -> bytes:
        """
        Decrypts and returns raw bytes.
        """
        data = json.loads(encrypted_data_str) if isinstance(encrypted_data_str, str) else encrypted_data_str
        ciphertext = base64.b64decode(data["ciphertext"])
        nonce = base64.b64decode(data["nonce"])
        tag = base64.b64decode(data["tag"])
        
        aesgcm = AESGCM(key)
        ciphertext_with_tag = ciphertext + tag
        return aesgcm.decrypt(nonce, ciphertext_with_tag, None)

class EnvelopeEncryptionService:
    @staticmethod
    def wrap_key(dek: bytes, kek: bytes) -> bytes:
        """
        Encrypt the DEK (Patient Key) using the KEK (Master Key).
        """
        aesgcm = AESGCM(kek)
        nonce = b"envelope_init" # deterministic or random (using random is safer but needs to be saved. We'll use random 12 bytes and prepend)
        nonce_rand = os.urandom(12)
        encrypted_dek = aesgcm.encrypt(nonce_rand, dek, None)
        return nonce_rand + encrypted_dek

    @staticmethod
    def unwrap_key(encrypted_dek: bytes, kek: bytes) -> bytes:
        """
        Decrypt the DEK using the KEK.
        """
        aesgcm = AESGCM(kek)
        nonce_rand = encrypted_dek[:12]
        ciphertext_with_tag = encrypted_dek[12:]
        return aesgcm.decrypt(nonce_rand, ciphertext_with_tag, None)

class PatientVaultKeyManager:
    @staticmethod
    def generate_patient_key() -> bytes:
        """
        Generate a unique 256-bit AES key.
        """
        return AESGCM.generate_key(bit_length=256)
