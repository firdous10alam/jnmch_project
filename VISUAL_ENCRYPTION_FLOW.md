# 🔐 Visual Encryption & Decryption Flow

## UPLOAD: Encryption Process

```
┌─────────────────────────────────────────────────────────────────┐
│                    UPLOAD ENCRYPTION                           │
└─────────────────────────────────────────────────────────────────┘

INPUT:
┌──────────────────────────────────────────────────────────────────┐
│ Original File: blood_test.pdf                                    │
│ Size: 1,000,000 bytes                                            │
│ Content: %PDF-1.4 ... [binary PDF data] ...                      │
│ Status: UNENCRYPTED (readable)                                   │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 1: Read File
┌──────────────────────────────────────────────────────────────────┐
│ uploaded_file.read()                                             │
│ Returns: 1,000,000 bytes of unencrypted data                     │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 2: Generate Encryption Key
┌──────────────────────────────────────────────────────────────────┐
│ key_material = SHA256(SECRET_KEY + "report-file")                │
│                                                                  │
│ Example:                                                         │
│ SECRET_KEY = "django-insecure-xk1bhdl_rray*1v3#f3ro%qwb%r6^e4"  │
│ + "report-file"                                                  │
│ = "django-insecure-xk1bhdl_rray*1v3#f3ro%qwb%r6^e4report-file"  │
│                                                                  │
│ SHA256 Hash: a7f3e9c2b1d4f6a8e9c2b1d4f6a8e9c2b1d4f6a8e9c2b1d4f6a8
│ (32 bytes)                                                       │
│                                                                  │
│ Base64 Encoded: YTdmM2U5YzJiMWQ0ZjZhOGU5YzJiMWQ0ZjZhOGU5YzJiMWQ0
│ (44 characters)                                                  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 3: Create Fernet Cipher
┌──────────────────────────────────────────────────────────────────┐
│ cipher = Fernet(base64_encoded_key)                              │
│                                                                  │
│ Fernet provides:                                                 │
│ • AES-128 encryption (symmetric)                                 │
│ • HMAC authentication                                            │
│ • Timestamp                                                      │
│ • IV (Initialization Vector)                                     │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 4: Encrypt Data
┌──────────────────────────────────────────────────────────────────┐
│ encrypted_bytes = cipher.encrypt(unencrypted_bytes)              │
│                                                                  │
│ Input:  %PDF-1.4 ... [1,000,000 bytes] ...                       │
│ Output: gAAAAABn7x8k...encrypted...kJ3xK9mL2pQ (1,000,016 bytes)│
│                                                                  │
│ Overhead: 16 bytes (IV + timestamp + HMAC)                       │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
OUTPUT:
┌──────────────────────────────────────────────────────────────────┐
│ Encrypted File: blood_test.pdf.enc                               │
│ Size: 1,000,016 bytes                                            │
│ Content: gAAAAABn7x8k...encrypted...kJ3xK9mL2pQ                 │
│ Status: ENCRYPTED (unreadable without key)                       │
│ Location: media/reports/2026/02/blood_test.pdf.enc               │
└──────────────────────────────────────────────────────────────────┘
```

---

## DOWNLOAD: Decryption Process

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOWNLOAD DECRYPTION                          │
└─────────────────────────────────────────────────────────────────┘

INPUT:
┌──────────────────────────────────────────────────────────────────┐
│ Encrypted File: blood_test.pdf.enc                               │
│ Size: 1,000,016 bytes                                            │
│ Content: gAAAAABn7x8k...encrypted...kJ3xK9mL2pQ                 │
│ Location: media/reports/2026/02/blood_test.pdf.enc               │
│ Status: ENCRYPTED (unreadable)                                   │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 1: Read Encrypted File
┌──────────────────────────────────────────────────────────────────┐
│ with report.file.open("rb") as f:                                │
│     encrypted_bytes = f.read()                                   │
│                                                                  │
│ Returns: 1,000,016 bytes of encrypted data                       │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 2: Generate Same Encryption Key
┌──────────────────────────────────────────────────────────────────┐
│ key_material = SHA256(SECRET_KEY + "report-file")                │
│                                                                  │
│ IMPORTANT: Must be SAME key as encryption!                       │
│ If SECRET_KEY changes, decryption fails!                         │
│                                                                  │
│ SHA256 Hash: a7f3e9c2b1d4f6a8e9c2b1d4f6a8e9c2b1d4f6a8e9c2b1d4f6a8
│ (32 bytes)                                                       │
│                                                                  │
│ Base64 Encoded: YTdmM2U5YzJiMWQ0ZjZhOGU5YzJiMWQ0ZjZhOGU5YzJiMWQ0
│ (44 characters)                                                  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 3: Create Same Fernet Cipher
┌──────────────────────────────────────────────────────────────────┐
│ cipher = Fernet(base64_encoded_key)                              │
│                                                                  │
│ Same cipher as encryption (same key)                             │
│ Fernet verifies:                                                 │
│ • HMAC signature                                                 │
│ • Timestamp                                                      │
│ • IV                                                             │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 4: Decrypt Data
┌──────────────────────────────────────────────────────────────────┐
│ decrypted_bytes = cipher.decrypt(encrypted_bytes)                │
│                                                                  │
│ Input:  gAAAAABn7x8k...encrypted...kJ3xK9mL2pQ (1,000,016 bytes)│
│ Output: %PDF-1.4 ... [1,000,000 bytes] ...                       │
│                                                                  │
│ Fernet verifies HMAC before decrypting                           │
│ If HMAC invalid → InvalidToken exception                         │
└──────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
            ✅ SUCCESS            ❌ FAILED
                    │                   │
                    │                   ▼
                    │         ┌──────────────────────┐
                    │         │ InvalidToken Error   │
                    │         │ File corrupted or    │
                    │         │ wrong key            │
                    │         │ Return 500 Error     │
                    │         └──────────────────────┘
                    │
                    ▼
OUTPUT:
┌──────────────────────────────────────────────────────────────────┐
│ Decrypted File: blood_test.pdf                                   │
│ Size: 1,000,000 bytes                                            │
│ Content: %PDF-1.4 ... [original PDF data] ...                    │
│ Status: UNENCRYPTED (readable)                                   │
│ Sent to: User's browser as download                              │
└──────────────────────────────────────────────────────────────────┘
```

---

## Key Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│              ENCRYPTION vs DECRYPTION KEY                       │
└─────────────────────────────────────────────────────────────────┘

ENCRYPTION:
  SECRET_KEY = "django-insecure-xk1bhdl_rray*1v3#f3ro%qwb%r6^e4"
  + "report-file"
  = "django-insecure-xk1bhdl_rray*1v3#f3ro%qwb%r6^e4report-file"
  ↓
  SHA256 Hash
  ↓
  Base64 Encode
  ↓
  Fernet Cipher
  ↓
  ENCRYPT

DECRYPTION:
  SECRET_KEY = "django-insecure-xk1bhdl_rray*1v3#f3ro%qwb%r6^e4"
  + "report-file"
  = "django-insecure-xk1bhdl_rray*1v3#f3ro%qwb%r6^e4report-file"
  ↓
  SHA256 Hash (SAME!)
  ↓
  Base64 Encode (SAME!)
  ↓
  Fernet Cipher (SAME!)
  ↓
  DECRYPT

✅ SAME KEY = Successful decryption
❌ DIFFERENT KEY = InvalidToken error
```

---

## File Transformation

```
┌─────────────────────────────────────────────────────────────────┐
│                    FILE TRANSFORMATION                          │
└─────────────────────────────────────────────────────────────────┘

UPLOAD:
  blood_test.pdf (1 MB)
       ↓
  [ENCRYPT]
       ↓
  blood_test.pdf.enc (1 MB + 16 bytes)
       ↓
  Saved to: media/reports/2026/02/blood_test.pdf.enc
       ↓
  Database: file = "reports/2026/02/blood_test.pdf.enc"

DOWNLOAD:
  media/reports/2026/02/blood_test.pdf.enc
       ↓
  [DECRYPT]
       ↓
  blood_test.pdf (1 MB)
       ↓
  Sent to: User's browser
       ↓
  User receives: Original blood_test.pdf
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLETE DATA FLOW                           │
└─────────────────────────────────────────────────────────────────┘

UPLOAD FLOW:
┌──────────────┐
│ Lab Tech     │
│ Uploads File │
└──────┬───────┘
       │ blood_test.pdf (unencrypted)
       ▼
┌──────────────────────────────────────────┐
│ ReportUploadSerializer.create()          │
│ (reports/serializers.py, line 54-67)     │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ encrypt_report_bytes()                   │
│ (reports/file_crypto.py, line 11-12)     │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ _report_file_cipher()                    │
│ (reports/file_crypto.py, line 6-8)       │
│ • SHA256(SECRET_KEY + "report-file")     │
│ • Base64 encode                          │
│ • Create Fernet cipher                   │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ Fernet.encrypt(data)                     │
│ • AES-128 encryption                     │
│ • HMAC authentication                    │
│ • Add IV + timestamp                     │
└──────┬───────────────────────────────────┘
       │ encrypted bytes
       ▼
┌──────────────────────────────────────────┐
│ Save to Disk                             │
│ media/reports/2026/02/blood_test.pdf.enc │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ Save to Database                         │
│ file = "reports/2026/02/blood_test.pdf.enc"
│ status = "pending"                       │
└──────────────────────────────────────────┘

DOWNLOAD FLOW:
┌──────────────┐
│ Patient      │
│ Requests     │
│ Download     │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ DownloadReportView.get()                 │
│ (reports/views.py, line 155-180)         │
│ • Check authentication                   │
│ • Validate access                        │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ Read Encrypted File                      │
│ media/reports/2026/02/blood_test.pdf.enc │
└──────┬───────────────────────────────────┘
       │ encrypted bytes
       ▼
┌──────────────────────────────────────────┐
│ decrypt_report_bytes()                   │
│ (reports/file_crypto.py, line 14-15)     │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ _report_file_cipher()                    │
│ (reports/file_crypto.py, line 6-8)       │
│ • SHA256(SECRET_KEY + "report-file")     │
│ • Base64 encode                          │
│ • Create Fernet cipher (SAME KEY!)       │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ Fernet.decrypt(data)                     │
│ • Verify HMAC                            │
│ • Verify timestamp                       │
│ • Decrypt with AES-128                   │
└──────┬───────────────────────────────────┘
       │
   ┌───┴───┐
   │       │
   ▼       ▼
✅ OK  ❌ ERROR
   │       │
   │       ▼
   │   InvalidToken
   │   Exception
   │
   ▼
┌──────────────────────────────────────────┐
│ Log Access                               │
│ (ReportAccessAudit)                      │
│ • user: patient1                         │
│ • status: success                        │
│ • ip: 192.168.1.100                      │
└──────┬───────────────────────────────────┘
       │ decrypted bytes
       ▼
┌──────────────────────────────────────────┐
│ Send to User                             │
│ HttpResponse(decrypted_bytes)            │
│ Content-Type: application/pdf            │
│ Content-Disposition: attachment          │
└──────┬───────────────────────────────────┘
       │ blood_test.pdf (unencrypted)
       ▼
┌──────────────────────────────────────────┐
│ Patient Receives File                    │
│ blood_test.pdf (original)                │
└──────────────────────────────────────────┘
```

---

**Version:** 1.0.0
**Date:** 2026-02-06
