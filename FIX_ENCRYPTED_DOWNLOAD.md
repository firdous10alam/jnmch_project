# FIX: File Still Encrypted When Downloading

## Problem
When downloading a report, the file was still in `.enc` format (encrypted) instead of being decrypted.

## Root Cause
The report status was **"pending"** instead of **"downloadable"**.

Access control rule:
```python
# File: reports/access_control.py, line 24
if report.status != "downloadable":
    return False, "Report is not downloadable yet"
```

**Patients can ONLY download reports with status = "downloadable"**

## Solution

### Step 1: Doctor Must Approve Report
Before a patient can download, a doctor must approve it:

```bash
POST /api/reports/{report_id}/verify/
Authorization: Bearer <DOCTOR_JWT_TOKEN>
```

This changes status from "pending" → "downloadable"

### Step 2: Then Patient Can Download
```bash
GET /api/reports/{report_id}/download/
Authorization: Bearer <PATIENT_JWT_TOKEN>
```

Now the file will be:
1. ✅ Decrypted
2. ✅ Sent as original PDF (not .enc)

## How It Works

### Upload (Lab Tech)
```
1. Lab tech uploads: blood_test.pdf
2. File encrypted: blood_test.pdf.enc
3. Saved to disk: media/reports/2026/02/blood_test.pdf.enc
4. Status: "pending"
5. Waiting for doctor approval
```

### Approval (Doctor)
```
1. Doctor views report
2. Doctor clicks "Approve" or calls /verify/ endpoint
3. Status changes: "pending" → "downloadable"
4. Patient notified
```

### Download (Patient)
```
1. Patient requests: GET /api/reports/1/download/
2. Access check: Is status "downloadable"? YES
3. Read encrypted file: media/reports/2026/02/blood_test.pdf.enc
4. Decrypt: decrypt_report_bytes(encrypted_bytes)
5. Send: Original blood_test.pdf (DECRYPTED)
```

## Testing

### Approve All Pending Reports
```bash
python approve_reports.py
```

### Test Download
```bash
# 1. Get patient token
TOKEN=$(curl -s -X POST http://localhost:8000/api/accounts/token/ \
  -d '{"username":"patient1","password":"Patient@123"}' | jq -r '.access')

# 2. Download report
curl -X GET http://localhost:8000/api/reports/1/download/ \
  -H "Authorization: Bearer $TOKEN" \
  -o downloaded_file.pdf

# 3. Verify it's a real PDF
file downloaded_file.pdf
# Should show: PDF document, version 1.3
```

## Access Control Rules

### Patient Download
```python
# File: reports/access_control.py, lines 8-24
def can_patient_access(user, report):
    # Check 1: Is this my report?
    if report.patient_id != patient.pk:
        return False, "Not authorized for this report"
    
    # Check 2: Is it downloadable?
    if report.status != "downloadable":
        return False, "Report is not downloadable yet"
    
    return True, None
```

### Doctor Download
```python
# File: reports/access_control.py, lines 26-28
def can_doctor_access(user, report):
    # Doctors can download ANY report
    return True, None
```

### Lab Technician Download
```python
# File: reports/access_control.py, lines 30-33
def can_lab_technician_access(user, report):
    # Can only download reports they uploaded
    if report.uploaded_by_id != user.id:
        return False, "Not authorized for this report"
    return True, None
```

## Encryption/Decryption Verification

### Test Encryption Works
```bash
python test_decrypt.py
```

Output:
```
ENCRYPTION/DECRYPTION TEST
============================================================

1. Original data:
   Size: 25 bytes
   Content: b'%PDF-1.4\nTest PDF content'

2. Encrypted data:
   Size: 120 bytes
   Content: b'gAAAAABph9JMh-xvAnbMD3SyE2g3Qn2VhX0NLzeZ_sE9-lvfhW'

3. Decrypted data:
   Size: 25 bytes
   Content: b'%PDF-1.4\nTest PDF content'

SUCCESS: Encryption/Decryption working correctly!
```

### Test Download Works
```bash
python test_download.py
```

Output:
```
Report: your report
Status: downloadable
File path: reports/2026/02/AMU_Hackathon_2026_1.pdf.enc

Encrypted file size: 1263652 bytes
Encrypted first 50 chars: b'gAAAAABph9FImT0tWbsTvGMhF2hzpo_MYQVxZO6f6XmFQ3qEPe'

Decrypted file size: 947668 bytes
Decrypted first 50 bytes: b'%PDF-1.3\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< \n/Creator (Canon SC1011)'

SUCCESS: File is a valid PDF!
```

## Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLETE WORKFLOW                            │
└─────────────────────────────────────────────────────────────────┘

1. LAB TECH UPLOADS
   ├─ POST /api/reports/upload/
   ├─ File: blood_test.pdf (unencrypted)
   ├─ Encrypted: blood_test.pdf.enc
   ├─ Saved: media/reports/2026/02/blood_test.pdf.enc
   └─ Status: "pending"

2. DOCTOR APPROVES
   ├─ POST /api/reports/1/verify/
   ├─ Status: "pending" → "downloadable"
   └─ Patient notified

3. PATIENT DOWNLOADS
   ├─ GET /api/reports/1/download/
   ├─ Access check: status == "downloadable"? YES
   ├─ Read encrypted file
   ├─ Decrypt: decrypt_report_bytes()
   ├─ Send: Original blood_test.pdf
   └─ User receives: DECRYPTED PDF
```

## Key Points

✅ **Encryption is working** - Files encrypted on upload
✅ **Decryption is working** - Files decrypted on download
✅ **Access control is working** - Only approved reports downloadable
✅ **Status matters** - Must be "downloadable" to download

## Files Involved

| File | Purpose |
|------|---------|
| reports/file_crypto.py | Encryption/Decryption |
| reports/serializers.py | Upload (calls encrypt) |
| reports/views.py | Download (calls decrypt) |
| reports/access_control.py | Access validation |
| reports/models.py | Report model with status |

## Next Steps

1. ✅ Approve pending reports: `python approve_reports.py`
2. ✅ Test download: `python test_download.py`
3. ✅ Download via API: Use patient token to download
4. ✅ Verify file is decrypted: Should be original PDF, not .enc

---

**Status:** FIXED
**Date:** 2026-02-06
