import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import migrations


def _report_file_cipher():
    key_material = hashlib.sha256((settings.SECRET_KEY + "report-file").encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key_material))


def forward_encrypt_existing_report_files(apps, schema_editor):
    Report = apps.get_model("reports", "Report")
    cipher = _report_file_cipher()

    for report in Report.objects.exclude(file="").iterator():
        if not report.file:
            continue

        name = report.file.name
        if not default_storage.exists(name):
            continue

        with default_storage.open(name, "rb") as f:
            data = f.read()

        # If decrypt succeeds, file is already encrypted.
        try:
            cipher.decrypt(data)
            continue
        except InvalidToken:
            pass

        encrypted = cipher.encrypt(data)
        new_name = name if name.endswith(".enc") else f"{name}.enc"
        saved_name = default_storage.save(new_name, ContentFile(encrypted))
        if saved_name != name and default_storage.exists(name):
            default_storage.delete(name)

        report.file = saved_name
        report.save(update_fields=["file"])


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0003_alter_report_options"),
    ]

    operations = [
        migrations.RunPython(forward_encrypt_existing_report_files, migrations.RunPython.noop),
    ]
