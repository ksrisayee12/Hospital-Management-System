import hashlib

class IntegrityVerifier:
    @staticmethod
    def calculate_hash(content: str) -> str:
        """
        Generate SHA-256 hash of plaintext content.
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    @staticmethod
    def calculate_hash_bytes(raw_bytes: bytes) -> str:
        """
        Generate SHA-256 hash of raw binary data.
        """
        return hashlib.sha256(raw_bytes).hexdigest()

    @staticmethod
    def verify(content: str, expected_hash: str) -> bool:
        """
        Decrypt -> SHA-256(decrypted) -> compare with stored hash.
        """
        if not content or not expected_hash:
            return False
        return IntegrityVerifier.calculate_hash(content) == expected_hash

    @staticmethod
    def verify_bytes(raw_bytes: bytes, expected_hash: str) -> bool:
        """
        Verify binary integrity against a stored hash.
        """
        if not raw_bytes or not expected_hash:
            return False
        return IntegrityVerifier.calculate_hash_bytes(raw_bytes) == expected_hash
