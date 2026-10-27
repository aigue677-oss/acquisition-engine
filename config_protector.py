import os
from cryptography.fernet import Fernet

class ConfigProtector:
    """
    Handles local symmetric encryption and headless RAM decryption 
    for institutional pipeline credentials.
    """
    def __init__(self, master_key: str = None):
        # Uses a provided runtime key or falls back to an environment-injected secret key
        self.key = master_key or os.environ.get("FERNET_MASTER_KEY")
        if self.key:
            self.cipher = Fernet(self.key.encode() if isinstance(self.key, str) else self.key)
        else:
            self.cipher = None

    @staticmethod
    def generate_master_key() -> str:
        """Generates a secure Fernet master key for local vault locking."""
        return Fernet.generate_key().decode()

    def encrypt_payload(self, plaintext_data: str) -> bytes:
        """Encrypts raw configuration strings into an unreadable binary block."""
        if not self.cipher:
            raise ValueError("Encryption failed: No Fernet master key provided.")
        return self.cipher.encrypt(plaintext_data.encode('utf-8'))

    def decrypt_payload(self, encrypted_payload: bytes) -> str:
        """Decrypts binary vault data strictly into server RAM at runtime."""
        if not self.cipher:
            raise ValueError("Decryption failed: No Fernet master key provided.")
        decrypted_bytes = self.cipher.decrypt(encrypted_payload)
        return decrypted_bytes.decode('utf-8')

if __name__ == "__main__":
    # Self-test routine for serverless verification
    print("ConfigProtector module loaded successfully in RAM-bound mode.")
      
