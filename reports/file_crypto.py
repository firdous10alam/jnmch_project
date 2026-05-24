import base64
import hashlib

from cryptography.fernet import Fernet
from django.conf import settings


def _report_file_cipher() -> Fernet:
    key_material = hashlib.sha256((settings.SECRET_KEY + "report-file").encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key_material))


def encrypt_report_bytes(data: bytes) -> bytes:
    return _report_file_cipher().encrypt(data)


def decrypt_report_bytes(data: bytes) -> bytes:
    return _report_file_cipher().decrypt(data)
