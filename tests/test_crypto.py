"""Tests for envault.crypto encryption/decryption utilities."""

import pytest
from envault.crypto import encrypt, decrypt


PASSWORD = "super-secret-passphrase"
PLAINTEXT = "MY_API_KEY=abc123xyz"


def test_encrypt_returns_string():
    result = encrypt(PLAINTEXT, PASSWORD)
    assert isinstance(result, str)
    assert result != PLAINTEXT


def test_decrypt_round_trip():
    ciphertext = encrypt(PLAINTEXT, PASSWORD)
    recovered = decrypt(ciphertext, PASSWORD)
    assert recovered == PLAINTEXT


def test_encrypt_produces_unique_ciphertexts():
    """Each encryption call should produce a different ciphertext (random salt)."""
    c1 = encrypt(PLAINTEXT, PASSWORD)
    c2 = encrypt(PLAINTEXT, PASSWORD)
    assert c1 != c2


def test_decrypt_wrong_password_raises():
    ciphertext = encrypt(PLAINTEXT, PASSWORD)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(ciphertext, "wrong-password")


def test_decrypt_corrupted_payload_raises():
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt("notvalidbase64!!", PASSWORD)


def test_encrypt_empty_string():
    ciphertext = encrypt("", PASSWORD)
    assert decrypt(ciphertext, PASSWORD) == ""


def test_encrypt_unicode_value():
    unicode_val = "TOKEN=こんにちは🔑"
    ciphertext = encrypt(unicode_val, PASSWORD)
    assert decrypt(ciphertext, PASSWORD) == unicode_val
