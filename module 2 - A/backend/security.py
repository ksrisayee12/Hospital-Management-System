"""
MODULE 2 — PART B: AES-256 Encryption & Security Utilities
"""

import base64
import hashlib
import logging
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _derive_key(patient_id: str) -> bytes:
    """Derive a per-patient AES-256 key using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=f"{settings.aes_encryption_iv_salt}{patient_id}".encode(),
        iterations=200_000,
    )
    master = bytes.fromhex(settings.aes_encryption_key)
    return kdf.derive(master)


def encrypt_text(plaintext: str, patient_id: str) -> str:
    """AES-256-GCM encrypt, return base64 ciphertext with nonce prefix."""
    key = _derive_key(patient_id)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    combined = nonce + ct
    return base64.b64encode(combined).decode()


def decrypt_text(ciphertext_b64: str, patient_id: str) -> str:
    """AES-256-GCM decrypt."""
    key = _derive_key(patient_id)
    aesgcm = AESGCM(key)
    combined = base64.b64decode(ciphertext_b64)
    nonce, ct = combined[:12], combined[12:]
    return aesgcm.decrypt(nonce, ct, None).decode()


def hash_patient_collection_name(patient_id: str) -> str:
    """Deterministic, one-way ChromaDB collection name per patient."""
    h = hashlib.sha256(patient_id.encode()).hexdigest()[:16]
    return f"{settings.chroma_collection_prefix}{h}"
