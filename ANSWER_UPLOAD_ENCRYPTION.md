# ✅ ANSWER: What Happens When You Upload & Where Encryption Occurs

## TL;DR (Quick Answer)

**When you upload a report:**
1. Lab technician sends unencrypted PDF file
2. Django receives it in `ReportUploadSerializer.create()` (serializers.py, line 54-67)
3. File is encrypted using `encrypt_report_bytes()` (file_crypto.py, line 11-12)
4. Encrypted file saved to disk as `.enc` file
5. Database stores path to encrypted file
6. Original unencrypted file is NEVER stored

**When patient downloads:**
1. Access control checks if authorized
2. Encrypted file read from disk
3. File is decrypted using `decrypt_report_bytes()` (file_crypto.py, line 14-15)
4. Decrypted file sent to user
5. Access logged to audit trail

---

## UPLOAD: Step-by-Step

### Step 1: Lab Tech Sends File
```
POST /api/reports/upload/
Content-Type: multipart/form-data

Body:
  registration_id: "PAT001"
  test_name: "Blood Test"
  file: <binary PDF data - UNENCRYPTED>
```

### Step 2: Django Receives Request
```python
# File: reports/views.py
class UploadReportView(generics.CreateAPIView):
    def post(self, request):
        # 1. Check authentication
        # 2. Check user is lab_technician
        # 3. Call serializer.save()
```

### Step 3: Serializer Validates
```python
# File: reports/serializers.py, lines 40-52
def validate(self, attrs):
    registration_id = attrs.get('registration_id')
    patient = Patient.objects.filter(
        Q(registration_id=registration_id) | Q(uhid=registration_id)
    ).first()
    attrs['_patient'] = patient
    return attrs
```

### Step 4: ENCRYPTION HAPPENS HERE ⚡
```python
# File: reports/serializers.py, lines 54-67
def create(self, validated_data):
    patient = validated_data.pop('_patient')
    uploaded_file = validated_data.pop('file')
    
    # ⚡ THIS IS WHERE ENCRYPTION HAPPENS
    encrypted_content = encrypt_report_bytes(uploaded_file.read())
    encrypted_name = f"{uploaded_file.name}.enc"
    
    report = Report(
        patient=patient,
        uploaded_by=self.context['request'].user,
        status="pending",
        **validated_data
    )
    # Save encrypted file to disk
    report.file.save(encrypted_name, ContentFile(encrypted_content), save=False)
    report.save()
    return report
```

### Step 5: Encryption Function
```python
# File: reports/file_crypto.py, lines 11-12
def encrypt_report_bytes(data: bytes) -> bytes:
    return _report_file_cipher().encrypt(data)

# Where _report_file_cipher() is:
# File: reports/file_crypto.py, lines 6-8
def _report_file_cipher() -> Fernet:
    key_material = hashlib.sha256(
        (settings.SECRET_KEY + "report-file").encode()
    ).digest()
    return Fernet(base64.urlsafe_b64encode(key_material))
```

### Step 6: File Saved to Disk
```
Location: media/reports/2026/02/
Filename: blood_test.pdf.enc
Content: gAAAAABn7x8k...encrypted...kJ3xK9mL2pQ
Status: ENCRYPTED (unreadable without key)
```

### Step 7: Database Record
```
reports_report table:
  report_id: 1
  patient_id: 1
  uploaded_by_id: 5
  file: "reports/2026/02/blood_test.pdf.enc"
  status: "pending"
  uploaded_at: 2026-02-06 10:30:45
```

---

## DOWNLOAD: Step-by-Step

### Step 1: Patient Requests Download
```
GET /api/reports/1/download/
Authorization: Bearer <JWT_TOKEN>
```

### Step 2: Access Control Check
```python
# File: reports/views.py, lines 155-180
def get(self, request, report_id):
    report = Report.objects.get(report_id=report_id)
    
    # Check access
    authorized, error_msg = ReportAccessValidator.validate_access(
        request.user, report
    )
    
    if not authorized:
        # Log denied access
        ReportAccessValidator.log_access(
            report, request.user, "download", "denied", error_msg, ip
        )
        return Response({"error": error_msg}, status=403)
```

### Step 3: Read Encrypted File
```python
# File: reports/views.py, line 172
with report.file.open("rb") as f:
    encrypted_bytes = f.read()

# Reads from: media/reports/2026/02/blood_test.pdf.enc
# Content: gAAAAABn7x8k...encrypted...kJ3xK9mL2pQ
```

### Step 4: DECRYPTION HAPPENS HERE ⚡
```python
# File: reports/views.py, line 176
try:
    # ⚡ THIS IS WHERE DECRYPTION HAPPENS
    decrypted = decrypt_report_bytes(encrypted_bytes)
except InvalidToken:
    # File corrupted or wrong key
    return Response({"error": "Stored file is unreadable"}, status=500)
```

### Step 5: Decryption Function
```python
# File: reports/file_crypto.py, lines 14-15
def decrypt_report_bytes(data: bytes) -> bytes:
    return _report_file_cipher().decrypt(data)

# Uses SAME _report_file_cipher() with SAME key
# If key is different, InvalidToken exception is raised
```

### Step 6: Log Access
```python
# File: reports/views.py, line 185
ReportAccessValidator.log_access(
    report, request.user, "download", "success", ip_address=ip
)

# Creates ReportAccessAudit record:
#   user: patient1
#   status: success
#   ip: 192.168.1.100
#   accessed_at: 2026-02-06 10:35:22
```

### Step 7: Send to User
```python
# File: reports/views.py, lines 187-190
response = HttpResponse(decrypted, content_type="application/pdf")
response["Content-Disposition"] = 'attachment; filename="blood_test.pdf"'
return response

# User receives: Original unencrypted blood_test.pdf
```

---

## WHERE ENCRYPTION HAPPENS

### Upload Encryption
```
File: reports/serializers.py
Function: ReportUploadSerializer.create()
Lines: 54-67
Exact Line: encrypted_content = encrypt_report_bytes(uploaded_file.read())
```

### Encryption Logic
```
File: reports/file_crypto.py
Function: encrypt_report_bytes()
Lines: 11-12
Calls: _report_file_cipher().encrypt(data)
```

### Key Generation
```
File: reports/file_crypto.py
Function: _report_file_cipher()
Lines: 6-8
Key: SHA256(SECRET_KEY + "report-file")
Algorithm: Fernet (AES-128 CBC + HMAC)
```

---

## WHERE DECRYPTION HAPPENS

### Download Decryption
```
File: reports/views.py
Function: DownloadReportView.get()
Lines: 155-180
Exact Line: decrypted = decrypt_report_bytes(encrypted_bytes)
```

### Decryption Logic
```
File: reports/file_crypto.py
Function: decrypt_report_bytes()
Lines: 14-15
Calls: _report_file_cipher().decrypt(data)
```

### Key Generation (Same as Encryption)
```
File: reports/file_crypto.py
Function: _report_file_cipher()
Lines: 6-8
Key: SHA256(SECRET_KEY + "report-file")
Algorithm: Fernet (AES-128 CBC + HMAC)
```

---

## FILE LOCATIONS

### Where Encrypted Files Are Stored
```
Project Root: f:\jmnch_project-main\

Encrypted Files:
  media/
  └── reports/
      └── 2026/
          └── 02/
              ├── blood_test.pdf.enc
              ├── xray_report.pdf.enc
              └── lab_results.pdf.enc

Code Files:
  reports/
  ├── file_crypto.py          ← Encryption/Decryption
  ├── serializers.py          ← Upload (calls encrypt)
  ├── views.py                ← Download (calls decrypt)
  └── access_control.py       ← Access validation
```

### Settings Configuration
```python
# File: jnmch_project/settings.py, lines 130-131
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# BASE_DIR = f:\jmnch_project-main\
# MEDIA_ROOT = f:\jmnch_project-main\media\
```

---

## KEY POINTS

### Encryption Key
```python
# Same key used for both encryption and decryption
key_material = SHA256(SECRET_KEY + "report-file")

# If SECRET_KEY changes:
# ❌ Old files cannot be decrypted
# ❌ InvalidToken exception raised
# ✅ New files encrypted with new key
```

### File Transformation
```
Upload:
  blood_test.pdf (1 MB, unencrypted)
  ↓ [ENCRYPT]
  blood_test.pdf.enc (1 MB + 16 bytes, encrypted)
  ↓ [SAVE]
  media/reports/2026/02/blood_test.pdf.enc

Download:
  media/reports/2026/02/blood_test.pdf.enc (encrypted)
  ↓ [READ]
  encrypted_bytes
  ↓ [DECRYPT]
  blood_test.pdf (1 MB, unencrypted)
  ↓ [SEND]
  User receives original file
```

### Access Control
```
Before decryption, check:
  ✅ User authenticated (JWT token)
  ✅ User authorized (role-based)
  ✅ Patient owns report (if patient)
  ✅ Report is downloadable (if patient)
  ✅ User uploaded report (if lab tech)

If any check fails:
  ❌ Return 403 Forbidden
  ❌ Log denied access
  ❌ Do NOT decrypt file
```

---

## SUMMARY TABLE

| Step | Location | File | Function | Line |
|------|----------|------|----------|------|
| Upload | Serializer | serializers.py | create() | 58 |
| Encrypt | Crypto | file_crypto.py | encrypt_report_bytes() | 11-12 |
| Key Gen | Crypto | file_crypto.py | _report_file_cipher() | 6-8 |
| Save | Serializer | serializers.py | create() | 66 |
| Download | View | views.py | get() | 172 |
| Decrypt | Crypto | file_crypto.py | decrypt_report_bytes() | 14-15 |
| Key Gen | Crypto | file_crypto.py | _report_file_cipher() | 6-8 |
| Log | View | views.py | get() | 185 |

---

## COMPLETE FLOW DIAGRAM

```
UPLOAD:
Lab Tech
  ↓
POST /api/reports/upload/
  ↓
UploadReportView.post()
  ↓
ReportUploadSerializer.validate()
  ↓
ReportUploadSerializer.create()
  ├─ Read file: uploaded_file.read()
  ├─ Encrypt: encrypt_report_bytes(bytes)
  │   └─ Key: SHA256(SECRET_KEY + "report-file")
  │   └─ Cipher: Fernet (AES-128 CBC + HMAC)
  ├─ Save: report.file.save(encrypted_name, encrypted_bytes)
  └─ Database: file = "reports/2026/02/blood_test.pdf.enc"

DOWNLOAD:
Patient
  ↓
GET /api/reports/1/download/
  ↓
DownloadReportView.get()
  ├─ Check authentication
  ├─ Check authorization
  ├─ Read file: report.file.open("rb").read()
  ├─ Decrypt: decrypt_report_bytes(encrypted_bytes)
  │   └─ Key: SHA256(SECRET_KEY + "report-file") [SAME]
  │   └─ Cipher: Fernet (AES-128 CBC + HMAC) [SAME]
  ├─ Log: ReportAccessValidator.log_access()
  └─ Send: HttpResponse(decrypted_bytes)
  ↓
Patient receives original file
```

---

## IMPORTANT NOTES

1. **Original file never stored unencrypted** - Only encrypted version on disk
2. **Same key for encrypt/decrypt** - Derived from SECRET_KEY
3. **Access control before decryption** - Only authorized users can decrypt
4. **All access logged** - Audit trail with IP address
5. **Encryption overhead** - ~16 bytes per file (IV + HMAC)
6. **Key rotation** - If SECRET_KEY changes, old files cannot be decrypted

---

**Version:** 1.0.0
**Date:** 2026-02-06
