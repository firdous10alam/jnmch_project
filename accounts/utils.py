# accounts/utils.py
import base64
import hashlib
import hmac

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def aadhaar_tokenize(aadhaar_str: str) -> bytes:
    # HMAC-SHA256 of Aadhaar using secret key - stores bytes
    key = settings.SECRET_KEY.encode()
    return hmac.new(key, aadhaar_str.encode(), hashlib.sha256).digest()


def _aadhaar_cipher() -> Fernet:
    # Derive a stable 32-byte key from Django secret for symmetric encryption.
    key_material = hashlib.sha256((settings.SECRET_KEY + "aadhaar").encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key_material))


def encrypt_aadhaar(aadhaar_str: str) -> str:
    return _aadhaar_cipher().encrypt(aadhaar_str.encode()).decode()


def decrypt_aadhaar(encrypted_value: str) -> str | None:
    if not encrypted_value:
        return None
    try:
        return _aadhaar_cipher().decrypt(encrypted_value.encode()).decode()
    except (InvalidToken, ValueError, TypeError):
        return None


def otp_hash(otp: str) -> bytes:
    key = (settings.SECRET_KEY + "otp").encode()
    return hmac.new(key, otp.encode(), hashlib.sha256).digest()


def verify_otp_hash(otp: str, otp_hash_bytes: bytes) -> bool:
    return hmac.compare_digest(otp_hash(otp), otp_hash_bytes)
