# 🔍 Code Reference - Encryption & Decryption Locations

## ENCRYPTION (Upload)

### File: `reports/serializers.py`

**Location:** Lines 54-67 (ReportUploadSerializer.create method)

```python
def create(self, validated_data):
    patient = validated_data.pop('_patient')
    registration_id = validated_data.pop('registration_id')
    uploaded_file = validated_data.pop('file')
    
    # ⚡ ENCRYPTION HAPPENS HERE (Line 58)
    encrypted_content = encrypt_report_bytes(uploaded_file.read())
    encrypted_name = f"{uploaded_file.name}.enc"
    
    # Create report
    report = Report(
        patient=patient,
        uploaded_by=self.context['request'].user,
        status="pending",
        **validated_data
    )
    # Save encrypted file (Line 66)
    report.file.save(encrypted_name, ContentFile(encrypted_content), save=False)
    report.save()
    return report
```

**Key Line:** `encrypted_content = encrypt_report_bytes(uploaded_file.read())`

---

### File: `reports/file_crypto.py`

**Location:** Lines 11-12 (encrypt_report_bytes function)

```python
def encrypt_report_bytes(data: bytes) -> bytes:
    return _report_file_cipher().encrypt(data)
```

**What it does:**
1. Takes unencrypted bytes
2. Uses Fernet cipher (created by `_report_file_cipher()`)
3. Returns encrypted bytes

---

### File: `reports/file_crypto.py`

**Location:** Lines 6-8 (_report_file_cipher function)

```python
def _report_file_cipher() -> Fernet:
    key_material = hashlib.sha256((settings.SECRET_KEY + "report-file").encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key_material))
```

**What it does:**
1. Creates SHA256 hash of: `SECRET_KEY + "report-file"`
2. Base64 encodes the hash
3. Creates Fernet cipher with that key
4. Returns cipher object

---

## DECRYPTION (Download)

### File: `reports/views.py`

**Location:** Lines 155-180 (DownloadReportView.get method)

```python
def get(self, request, report_id):
    try:
        report = Report.objects.get(report_id=report_id)
    except Report.DoesNotExist:
        logger.warning("Report not found: report_id=%s, user=%s", report_id, request.user.username)
        return Response({"error": "Report not found"}, status=status.HTTP_404_NOT_FOUND)

    ip = self._get_client_ip(request)
    authorized, error_msg = ReportAccessValidator.validate_access(request.user, report)
    
    if not authorized:
        ReportAccessValidator.log_access(
            report, request.user, "download", "denied", error_msg, ip
        )
        logger.warning("Unauthorized access attempt: report_id=%s, user=%s, role=%s", 
                      report_id, request.user.username, getattr(request.user, "role", None))
        return Response({"error": error_msg}, status=status.HTTP_403_FORBIDDEN)

    # Read encrypted file (Line 172)
    with report.file.open("rb") as f:
        encrypted_bytes = f.read()

    try:
        # ⚡ DECRYPTION HAPPENS HERE (Line 176)
        decrypted = decrypt_report_bytes(encrypted_bytes)
    except InvalidToken:
        ReportAccessValidator.log_access(
            report, request.user, "download", "denied", "Decryption failed", ip
        )
        logger.exception("Failed to decrypt report file: report_id=%s, user=%s", 
                       report_id, request.user.username)
        return Response({"error": "Stored file is unreadable"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    ReportAccessValidator.log_access(
        report, request.user, "download", "success", ip_address=ip
    )
    logger.info("Report downloaded: report_id=%s, user=%s, role=%s", 
               report_id, request.user.username, getattr(request.user, "role", None))
    
    stored_name = os.path.basename(report.file.name)
    download_name = stored_name[:-4] if stored_name.endswith(".enc") else stored_name
    content_type = mimetypes.guess_type(download_name)[0] or "application/octet-stream"
    response = HttpResponse(decrypted, content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{download_name}"'
    return response
```

**Key Lines:**
- Line 172: `encrypted_bytes = f.read()` - Read encrypted file
- Line 176: `decrypted = decrypt_report_bytes(encrypted_bytes)` - Decrypt

---

### File: `reports/file_crypto.py`

**Location:** Lines 14-15 (decrypt_report_bytes function)

```python
def decrypt_report_bytes(data: bytes) -> bytes:
    return _report_file_cipher().decrypt(data)
```

**What it does:**
1. Takes encrypted bytes
2. Uses same Fernet cipher (created by `_report_file_cipher()`)
3. Returns decrypted bytes

---

## UPLOAD FLOW - STEP BY STEP

```
1. Lab Tech sends POST /api/reports/upload/
   └─ File: blood_test.pdf (unencrypted)

2. UploadReportView.post() (views.py)
   └─ Calls serializer.save()

3. ReportUploadSerializer.validate() (serializers.py, lines 40-52)
   └─ Finds patient by registration_id
   └─ Stores patient in attrs['_patient']

4. ReportUploadSerializer.create() (serializers.py, lines 54-67)
   └─ Line 58: encrypted_content = encrypt_report_bytes(uploaded_file.read())
      ├─ Calls encrypt_report_bytes() (file_crypto.py, line 11)
      │  └─ Calls _report_file_cipher().encrypt(data)
      │     └─ Uses Fernet cipher with SHA256 key
      └─ Returns encrypted bytes

5. Save encrypted file (serializers.py, line 66)
   └─ report.file.save(encrypted_name, ContentFile(encrypted_content))
   └─ Saved to: media/reports/2026/02/blood_test.pdf.enc

6. Save report to database (serializers.py, line 67)
   └─ report.save()
   └─ Status: "pending"

7. Return response to lab tech
   └─ HTTP 201 Created
   └─ File is now encrypted on disk
```

---

## DOWNLOAD FLOW - STEP BY STEP

```
1. Patient sends GET /api/reports/1/download/
   └─ With JWT token

2. DownloadReportView.get() (views.py, lines 155-180)
   └─ Get report from database

3. Access validation (views.py, line 164)
   └─ ReportAccessValidator.validate_access(user, report)
   └─ Check: Is this my report? Is it downloadable?

4. Read encrypted file (views.py, line 172)
   └─ with report.file.open("rb") as f:
   └─ encrypted_bytes = f.read()
   └─ Reads from: media/reports/2026/02/blood_test.pdf.enc

5. DECRYPT (views.py, line 176)
   └─ decrypted = decrypt_report_bytes(encrypted_bytes)
      ├─ Calls decrypt_report_bytes() (file_crypto.py, line 14)
      │  └─ Calls _report_file_cipher().decrypt(data)
      │     └─ Uses same Fernet cipher with same SHA256 key
      └─ Returns original unencrypted bytes

6. Log access (views.py, line 185)
   └─ ReportAccessValidator.log_access(...)
   └─ Creates ReportAccessAudit record

7. Send file to user (views.py, lines 187-190)
   └─ HttpResponse(decrypted, content_type=content_type)
   └─ User receives original unencrypted PDF
```

---

## KEY ENCRYPTION PARAMETERS

### Encryption Algorithm
```python
# File: reports/file_crypto.py, line 6-8
Algorithm: Fernet (AES-128 CBC + HMAC)
Key: SHA256(SECRET_KEY + "report-file")
Encoding: Base64 URL-safe
```

### Key Derivation
```python
# File: reports/file_crypto.py, line 7
key_material = hashlib.sha256(
    (settings.SECRET_KEY + "report-file").encode()
).digest()

# Example:
# SECRET_KEY = "django-insecure-xk1bhdl_rray*1v3#f3ro%qwb%r6^e4dbbslmzbin9z06ygk6q"
# key_material = SHA256("django-insecure-xk1bhdl_rray*1v3#f3ro%qwb%r6^e4dbbslmzbin9z06ygk6qreport-file")
# Result: 32-byte hash
```

### Fernet Cipher
```python
# File: reports/file_crypto.py, line 8
cipher = Fernet(base64.urlsafe_b64encode(key_material))

# Fernet provides:
# - Symmetric encryption (AES-128)
# - Authentication (HMAC)
# - Timestamp
# - IV (Initialization Vector)
```

---

## FILE STORAGE LOCATIONS

### Settings Configuration
```python
# File: jnmch_project/settings.py, lines 130-131
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# BASE_DIR = f:\jmnch_project-main\
# MEDIA_ROOT = f:\jmnch_project-main\media\
```

### Actual File Locations
```
f:\jmnch_project-main\
└── media\
    └── reports\
        └── 2026\
            └── 02\
                ├── blood_test.pdf.enc          ← ENCRYPTED
                ├── xray_report.pdf.enc         ← ENCRYPTED
                └── lab_results.pdf.enc         ← ENCRYPTED
```

### Database Record
```python
# File: reports/models.py
class Report(models.Model):
    file = models.FileField(upload_to="reports/%Y/%m/")
    
# Example database value:
# file = "reports/2026/02/blood_test.pdf.enc"
```

---

## IMPORTS NEEDED

### For Encryption
```python
# File: reports/file_crypto.py
import base64
import hashlib
from cryptography.fernet import Fernet
from django.conf import settings
```

### For Upload
```python
# File: reports/serializers.py
from django.core.files.base import ContentFile
from .file_crypto import encrypt_report_bytes
```

### For Download
```python
# File: reports/views.py
from cryptography.fernet import InvalidToken
from .file_crypto import decrypt_report_bytes
```

---

## ERROR HANDLING

### Encryption Errors
```python
# File: reports/serializers.py
# If encryption fails, exception is raised during upload
# Django handles it and returns 400 Bad Request
```

### Decryption Errors
```python
# File: reports/views.py, lines 177-183
try:
    decrypted = decrypt_report_bytes(encrypted_bytes)
except InvalidToken:
    # File is corrupted or key is wrong
    ReportAccessValidator.log_access(
        report, request.user, "download", "denied", "Decryption failed", ip
    )
    return Response(
        {"error": "Stored file is unreadable"}, 
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
```

---

## VERIFICATION COMMAND

### Check Encryption Status
```bash
# File: reports/management/commands/verify_report_encryption.py
python manage.py verify_report_encryption

# What it does:
# 1. Reads all report files
# 2. Tries to decrypt each one
# 3. Reports encryption status
# 4. Identifies corrupted files
```

### Fix Unencrypted Reports
```bash
python manage.py verify_report_encryption --fix

# What it does:
# 1. Finds unencrypted reports
# 2. Encrypts them
# 3. Saves encrypted versions
```

---

## SUMMARY

| Operation | File | Function | Line |
|-----------|------|----------|------|
| **Encrypt** | file_crypto.py | encrypt_report_bytes() | 11-12 |
| **Decrypt** | file_crypto.py | decrypt_report_bytes() | 14-15 |
| **Key Gen** | file_crypto.py | _report_file_cipher() | 6-8 |
| **Upload** | serializers.py | ReportUploadSerializer.create() | 54-67 |
| **Download** | views.py | DownloadReportView.get() | 155-180 |
| **Verify** | management/commands/verify_report_encryption.py | Command.handle() | - |

---

**Version:** 1.0.0
**Date:** 2026-02-06
