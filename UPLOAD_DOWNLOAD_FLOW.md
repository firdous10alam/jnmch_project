# 📊 Report Upload & Download Flow - Detailed Explanation

## UPLOAD FLOW (Where Encryption Happens)

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAB TECHNICIAN UPLOADS                       │
└─────────────────────────────────────────────────────────────────┘

STEP 1: Lab Technician Sends Request
┌──────────────────────────────────────────────────────────────────┐
│ POST /api/reports/upload/                                        │
│ Content-Type: multipart/form-data                                │
│                                                                  │
│ Body:                                                            │
│   - registration_id: "PAT001"                                    │
│   - test_name: "Blood Test"                                      │
│   - test_type: "Pathology"                                       │
│   - file: <binary PDF data>  ← UNENCRYPTED FILE                  │
│   - is_critical: false                                           │
│   - comments: "Routine checkup"                                  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 2: Django Receives Request
┌──────────────────────────────────────────────────────────────────┐
│ UploadReportView.post()                                          │
│ (reports/views.py)                                               │
│                                                                  │
│ 1. Check authentication (JWT token)                              │
│ 2. Check user role = "lab_technician"                            │
│ 3. Call serializer.save()                                        │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 3: Serializer Validation
┌──────────────────────────────────────────────────────────────────┐
│ ReportUploadSerializer.validate()                                │
│ (reports/serializers.py)                                         │
│                                                                  │
│ 1. Get registration_id from request                              │
│ 2. Find patient in database                                      │
│ 3. Store patient in attrs['_patient']                            │
│ 4. Return validated_data                                         │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 4: ENCRYPTION HAPPENS HERE ⚡
┌──────────────────────────────────────────────────────────────────┐
│ ReportUploadSerializer.create()                                  │
│ (reports/serializers.py, line 54-67)                             │
│                                                                  │
│ def create(self, validated_data):                                │
│     patient = validated_data.pop('_patient')                     │
│     uploaded_file = validated_data.pop('file')                   │
│                                                                  │
│     # ⚡ ENCRYPTION STEP                                         │
│     encrypted_content = encrypt_report_bytes(                    │
│         uploaded_file.read()  # Read unencrypted bytes           │
│     )                                                            │
│     encrypted_name = f"{uploaded_file.name}.enc"                 │
│                                                                  │
│     # Create report object                                       │
│     report = Report(                                             │
│         patient=patient,                                         │
│         uploaded_by=self.context['request'].user,                │
│         status="pending",                                        │
│         **validated_data                                         │
│     )                                                            │
│     # Save encrypted file                                        │
│     report.file.save(                                            │
│         encrypted_name,                                          │
│         ContentFile(encrypted_content),  # Encrypted bytes       │
│         save=False                                               │
│     )                                                            │
│     report.save()                                                │
│     return report                                                │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 5: Encryption Details
┌──────────────────────────────────────────────────────────────────┐
│ encrypt_report_bytes()                                           │
│ (reports/file_crypto.py, line 11-12)                             │
│                                                                  │
│ def encrypt_report_bytes(data: bytes) -> bytes:                  │
│     return _report_file_cipher().encrypt(data)                   │
│                                                                  │
│ Where _report_file_cipher() creates:                             │
│   1. key_material = SHA256(SECRET_KEY + "report-file")           │
│   2. Fernet cipher with base64-encoded key                       │
│   3. Returns encrypted bytes                                     │
│                                                                  │
│ Algorithm: Fernet (AES-128 CBC + HMAC)                           │
│ Key: Derived from Django SECRET_KEY                              │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 6: File Saved to Disk
┌──────────────────────────────────────────────────────────────────┐
│ Location: media/reports/2026/02/                                 │
│ Filename: <original_name>.enc                                    │
│ Content: ENCRYPTED BYTES (unreadable)                            │
│                                                                  │
│ Example:                                                         │
│   File: blood_test.pdf.enc                                       │
│   Size: ~same as original (encryption adds ~16 bytes overhead)   │
│   Content: gAAAAABn7x8k...encrypted data...                      │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 7: Database Record Created
┌──────────────────────────────────────────────────────────────────┐
│ reports_report table:                                            │
│                                                                  │
│ report_id: 1                                                     │
│ patient_id: 1                                                    │
│ uploaded_by_id: 5 (lab technician)                               │
│ test_name: "Blood Test"                                          │
│ test_type: "Pathology"                                           │
│ file: "reports/2026/02/blood_test.pdf.enc"                       │
│ status: "pending"  ← NOT YET DOWNLOADABLE                        │
│ uploaded_at: 2026-02-06 10:30:45                                 │
│ is_critical: false                                               │
│ comments: "Routine checkup"                                      │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 8: Response to Lab Technician
┌──────────────────────────────────────────────────────────────────┐
│ HTTP 201 Created                                                 │
│                                                                  │
│ {                                                                │
│   "report_id": 1,                                                │
│   "patient": 1,                                                  │
│   "test_name": "Blood Test",                                     │
│   "status": "pending",                                           │
│   "uploaded_at": "2026-02-06T10:30:45Z",                         │
│   "file": "/media/reports/2026/02/blood_test.pdf.enc"            │
│ }                                                                │
│                                                                  │
│ ✅ Upload Complete                                               │
│ ⏳ Waiting for doctor approval                                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## DOWNLOAD FLOW (Where Decryption Happens)

```
┌─────────────────────────────────────────────────────────────────┐
│                    PATIENT/DOCTOR DOWNLOADS                     │
└─────────────────────────────────────────────────────────────────┘

STEP 1: User Requests Download
┌──────────────────────────────────────────────────────────────────┐
│ GET /api/reports/1/download/                                     │
│ Headers:                                                         │
│   Authorization: Bearer <JWT_TOKEN>                              │
│   X-Forwarded-For: 192.168.1.100                                 │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 2: Access Control Check
┌──────────────────────────────────────────────────────────────────┐
│ DownloadReportView.get()                                         │
│ (reports/views.py)                                               │
│                                                                  │
│ 1. Get report from database                                      │
│ 2. Extract client IP: 192.168.1.100                              │
│ 3. Call ReportAccessValidator.validate_access()                  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 3: Access Validation
┌──────────────────────────────────────────────────────────────────┐
│ ReportAccessValidator.validate_access()                          │
│ (reports/access_control.py)                                      │
│                                                                  │
│ IF user.role == "patient":                                       │
│   ├─ Check: report.patient_id == user.patient_profile.id         │
│   ├─ Check: report.status == "downloadable"                      │
│   └─ Result: True/False                                          │
│                                                                  │
│ IF user.role == "doctor":                                        │
│   └─ Result: True (all reports allowed)                          │
│                                                                  │
│ IF user.role == "lab_technician":                                │
│   ├─ Check: report.uploaded_by_id == user.id                     │
│   └─ Result: True/False                                          │
└──────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
            ✅ AUTHORIZED        ❌ DENIED
                    │                   │
                    │                   ▼
                    │         ┌──────────────────────┐
                    │         │ Log Denied Access    │
                    │         │ (ReportAccessAudit)  │
                    │         │                      │
                    │         │ user: patient1       │
                    │         │ status: denied       │
                    │         │ reason: "Not auth"   │
                    │         │ ip: 192.168.1.100    │
                    │         └──────────────────────┘
                    │                   │
                    │                   ▼
                    │         Return 403 Forbidden
                    │
                    ▼
STEP 4: Read Encrypted File from Disk
┌──────────────────────────────────────────────────────────────────┐
│ with report.file.open("rb") as f:                                │
│     encrypted_bytes = f.read()                                   │
│                                                                  │
│ File: media/reports/2026/02/blood_test.pdf.enc                   │
│ Content: gAAAAABn7x8k...encrypted data...                        │
│ Size: ~same as original                                          │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 5: DECRYPTION HAPPENS HERE ⚡
┌──────────────────────────────────────────────────────────────────┐
│ decrypt_report_bytes()                                           │
│ (reports/file_crypto.py, line 14-15)                             │
│                                                                  │
│ def decrypt_report_bytes(data: bytes) -> bytes:                  │
│     return _report_file_cipher().decrypt(data)                   │
│                                                                  │
│ Where _report_file_cipher() uses:                                │
│   1. Same key_material = SHA256(SECRET_KEY + "report-file")      │
│   2. Same Fernet cipher                                          │
│   3. Decrypts encrypted bytes                                    │
│   4. Returns original unencrypted bytes                          │
│                                                                  │
│ Input:  gAAAAABn7x8k...encrypted data...                         │
│ Output: %PDF-1.4...original PDF content...                       │
└──────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
            ✅ SUCCESS            ❌ FAILED
                    │                   │
                    │                   ▼
                    │         ┌──────────────────────┐
                    │         │ Log Failed Decrypt   │
                    │         │ (ReportAccessAudit)  │
                    │         │                      │
                    │         │ status: denied       │
                    │         │ reason: "Decrypt err"│
                    │         └──────────────────────┘
                    │                   │
                    │                   ▼
                    │         Return 500 Error
                    │
                    ▼
STEP 6: Log Successful Access
┌──────────────────────────────────────────────────────────────────┐
│ ReportAccessValidator.log_access()                               │
│ (reports/access_control.py)                                      │
│                                                                  │
│ ReportAccessAudit.objects.create(                                │
│     report=report,                                               │
│     user=user,                                                   │
│     access_type="download",                                      │
│     status="success",                                            │
│     ip_address="192.168.1.100",                                  │
│     accessed_at=now()                                            │
│ )                                                                │
│                                                                  │
│ Database record created for audit trail                          │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 7: Send Decrypted File to User
┌──────────────────────────────────────────────────────────────────┐
│ HttpResponse(decrypted, content_type="application/pdf")          │
│                                                                  │
│ Headers:                                                         │
│   Content-Type: application/pdf                                  │
│   Content-Disposition: attachment; filename="blood_test.pdf"     │
│                                                                  │
│ Body: %PDF-1.4...original PDF content...                         │
│                                                                  │
│ ✅ Download Complete                                             │
│ User receives original unencrypted PDF                           │
└──────────────────────────────────────────────────────────────────┘
```

---

## KEY POINTS

### Encryption (Upload)
```
Original File (Unencrypted)
    ↓
    ├─ Read bytes: uploaded_file.read()
    ├─ Encrypt: encrypt_report_bytes(bytes)
    │   └─ Uses: Fernet cipher with SHA256(SECRET_KEY + "report-file")
    ├─ Save: report.file.save(encrypted_name, ContentFile(encrypted_bytes))
    └─ Stored: media/reports/2026/02/filename.enc (ENCRYPTED)
```

### Decryption (Download)
```
Encrypted File (On Disk)
    ↓
    ├─ Read bytes: report.file.open("rb").read()
    ├─ Decrypt: decrypt_report_bytes(bytes)
    │   └─ Uses: Same Fernet cipher with same key
    ├─ Return: Original unencrypted bytes
    └─ Send: HttpResponse(decrypted_bytes)
```

### Key Derivation
```python
# Same key used for both encryption and decryption
key_material = SHA256(SECRET_KEY + "report-file")
cipher = Fernet(base64.urlsafe_b64encode(key_material))

# If SECRET_KEY changes, old files cannot be decrypted!
```

---

## FILE LOCATIONS

### Where Files Are Stored
```
Project Root: f:\jmnch_project-main\

ENCRYPTED FILES:
  media/
  └── reports/
      └── 2026/
          └── 02/
              ├── blood_test.pdf.enc          ← ENCRYPTED
              ├── xray_report.pdf.enc         ← ENCRYPTED
              └── lab_results.pdf.enc         ← ENCRYPTED

CODE FILES:
  reports/
  ├── file_crypto.py                  ← Encryption/Decryption logic
  ├── serializers.py                  ← Upload serializer (calls encrypt)
  ├── views.py                        ← Download view (calls decrypt)
  └── access_control.py               ← Access validation

DATABASE:
  db.sqlite3 (or MySQL)
  └── reports_report table
      └── file field = "reports/2026/02/blood_test.pdf.enc"
```

---

## SETTINGS CONFIGURATION

```python
# settings.py

# Where encrypted files are stored
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

# Encryption key source
SECRET_KEY = "your-secret-key-here"

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

---

## EXAMPLE: Complete Upload & Download Cycle

### Upload
```
1. Lab Tech uploads: blood_test.pdf (1 MB)
2. Serializer reads file: 1,000,000 bytes
3. Encryption: encrypt_report_bytes(1,000,000 bytes)
4. Encrypted: ~1,000,016 bytes (16 bytes overhead)
5. Saved as: media/reports/2026/02/blood_test.pdf.enc
6. Database: file = "reports/2026/02/blood_test.pdf.enc"
7. Status: "pending" (waiting for doctor approval)
```

### Doctor Approves
```
1. Doctor marks report as downloadable
2. Status changes: "pending" → "downloadable"
3. Patient receives notification
```

### Download
```
1. Patient requests: GET /api/reports/1/download/
2. Access check: Is this my report? Is it downloadable?
3. Read file: media/reports/2026/02/blood_test.pdf.enc
4. Decrypt: decrypt_report_bytes(encrypted_bytes)
5. Result: Original 1,000,000 bytes
6. Send: HttpResponse with PDF content
7. Log: ReportAccessAudit record created
8. Patient receives: blood_test.pdf (original file)
```

---

## SECURITY SUMMARY

✅ **At Rest:** Files encrypted on disk (.enc files)
✅ **In Transit:** HTTPS (recommended for production)
✅ **In Memory:** Decrypted only when needed
✅ **Access Control:** Only authorized users can decrypt
✅ **Audit Trail:** All access logged with IP
✅ **Key Management:** Derived from SECRET_KEY

---

**Version:** 1.0.0
**Date:** 2026-02-06
