import base64
import hashlib
import hmac

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import migrations


def _aadhaar_cipher():
    key_material = hashlib.sha256((settings.SECRET_KEY + "aadhaar").encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key_material))


def _aadhaar_tokenize(aadhaar_str):
    key = settings.SECRET_KEY.encode()
    return hmac.new(key, aadhaar_str.encode(), hashlib.sha256).digest()


def _decrypt_if_possible(cipher, value):
    try:
        return cipher.decrypt(value.encode()).decode()
    except (InvalidToken, ValueError, TypeError, AttributeError):
        return None


def forward_encrypt_aadhaar(apps, schema_editor):
    Patient = apps.get_model("accounts", "Patient")
    User = apps.get_model("accounts", "User")
    cipher = _aadhaar_cipher()

    patients = Patient.objects.exclude(aadhaar__isnull=True).exclude(aadhaar="")
    for patient in patients.iterator():
        raw_value = (patient.aadhaar or "").strip()
        if not raw_value:
            continue

        decrypted = _decrypt_if_possible(cipher, raw_value)
        plain = decrypted if decrypted is not None else raw_value
        normalized = plain.replace(" ", "")

        # Aadhaar should be numeric; skip malformed historical values.
        if not normalized.isdigit():
            continue

        encrypted = cipher.encrypt(normalized.encode()).decode()
        patient.aadhaar = encrypted
        patient.save(update_fields=["aadhaar"])

        user = User.objects.filter(pk=patient.user_id).first()
        if user and not user.aadhaar_token:
            user.aadhaar_token = _aadhaar_tokenize(normalized)
            user.save(update_fields=["aadhaar_token"])


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_alter_patient_aadhaar_alter_user_aadhaar_token"),
    ]

    operations = [
        migrations.RunPython(forward_encrypt_aadhaar, migrations.RunPython.noop),
    ]
