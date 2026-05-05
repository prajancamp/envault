"""Cryptographic utilities for encrypting and decrypting environment variable values."""

import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

SALT_SIZE = 16
KDF_ITERATIONS = 390_000


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a Fernet-compatible key from a password and salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def encrypt(plaintext: str, password: str) -> str:
    """Encrypt a plaintext string with a password.

    Returns a base64-encoded string containing the salt and ciphertext.
    """
    salt = os.urandom(SALT_SIZE)
    key = _derive_key(password, salt)
    token = Fernet(key).encrypt(plaintext.encode())
    payload = base64.urlsafe_b64encode(salt + token)
    return payload.decode()


def decrypt(payload: str, password: str) -> str:
    """Decrypt a payload produced by :func:`encrypt`.

    Raises:
        ValueError: if decryption fails (wrong password or corrupted data).
    """
    try:
        raw = base64.urlsafe_b64decode(payload.encode())
        salt, token = raw[:SALT_SIZE], raw[SALT_SIZE:]
        key = _derive_key(password, salt)
        return Fernet(key).decrypt(token).decode()
    except Exception as exc:
        raise ValueError("Decryption failed: invalid password or corrupted data.") from exc
