# Security Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    JNMCH Report Portal                          │
│                   Security Architecture                         │
└─────────────────────────────────────────────────────────────────┘

                          ┌──────────────┐
                          │   Patient    │
                          │   Doctor     │
                          │   Lab Tech   │
                          │   Admin      │
                          └──────┬───────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
            ┌───────▼────────┐      ┌────────▼──────┐
            │  Authentication│      │  Authorization│
            │  (JWT Tokens)  │      │  (RBAC)       │
            └───────┬────────┘      └────────┬──────┘
                    │                        │
                    └────────────┬───────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  ReportAccessValidator  │
                    │  (Centralized Control)  │
                    └────────────┬────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
        ┌───────▼──────┐  ┌──────▼──────┐  ┌────▼──────────┐
        │   Patient    │  │   Doctor    │  │  Lab Tech     │
        │   Access     │  │   Access    │  │   Access      │
        │   Rules      │  │   Rules     │  │   Rules       │
        └───────┬──────┘  └──────┬──────┘  └────┬──────────┘
                │                │              │
                └────────────────┼──────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Report File Access    │
                    │  (Encrypted Storage)   │
                    └────────────┬────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
        ┌───────▼──────┐  ┌──────▼──────┐  ┌────▼──────────┐
        │  Encryption  │  │  Decryption │  │  Audit Log    │
        │  (Fernet)    │  │  (Fernet)   │  │  (Database)   │
        └───────┬──────┘  └──────┬──────┘  └────┬──────────┘
                │                │              │
                └────────────────┼──────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  ReportAccessAudit     │
                    │  (Audit Trail)         │
                    │  - User                │
                    │  - Access Type         │
                    │  - Status              │
                    │  - IP Address          │
                    │  - Timestamp           │
                    └────────────────────────┘
```

## Access Control Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Request Flow                            │
└─────────────────────────────────────────────────────────────────┘

    User Request
         │
         ▼
    ┌─────────────────┐
    │ Authentication  │
    │ (JWT Token)     │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ ReportAccessValidator.validate_access│
    └────────┬────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌──────────┐    ┌──────────────┐
│ Patient? │    │ Doctor?      │
└────┬─────┘    └────┬─────────┘
     │               │
     ▼               ▼
┌──────────────┐  ┌──────────────┐
│ Own Report?  │  │ All Reports  │
│ Approved?    │  │ Allowed      │
└────┬─────────┘  └────┬─────────┘
     │                 │
     ├─────────┬───────┤
     │         │       │
     ▼         ▼       ▼
  ✅ YES    ❌ NO    ✅ YES
     │         │       │
     │         ▼       │
     │    ┌─────────────┐
     │    │ Log Denied  │
     │    │ Return 403  │
     │    └─────────────┘
     │
     ▼
┌──────────────────┐
│ Read Encrypted   │
│ File             │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Decrypt File     │
│ (Fernet)         │
└────────┬─────────┘
         │
    ┌────┴────┐
    │          │
    ▼          ▼
✅ OK      ❌ ERROR
    │          │
    │          ▼
    │     ┌──────────────┐
    │     │ Log Failed   │
    │     │ Return 500   │
    │     └──────────────┘
    │
    ▼
┌──────────────────┐
│ Log Success      │
│ Return File      │
└──────────────────┘
```

## Database Schema

```
┌─────────────────────────────────────────────────────────────────┐
│                    Database Tables                              │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│   auth_user          │
├──────────────────────┤
│ id (PK)              │
│ username             │
│ password             │
│ role                 │
│ phone                │
│ aadhaar_token        │
│ uhid                 │
└──────────────────────┘
         │
         ├─────────────────────────────────┐
         │                                 │
         ▼                                 ▼
┌──────────────────────┐      ┌──────────────────────┐
│   accounts_patient   │      │   accounts_doctor    │
├──────────────────────┤      ├──────────────────────┤
│ user_id (FK, PK)     │      │ user_id (FK, PK)     │
│ registration_id      │      │ doctor_reg_no        │
│ uhid                 │      │ specialization       │
│ aadhaar              │      └──────────────────────┘
│ dob                  │
│ gender               │
│ email                │
│ phone                │
└──────────────────────┘

┌──────────────────────┐
│   reports_report     │
├──────────────────────┤
│ report_id (PK)       │
│ patient_id (FK)      │◄─────────┐
│ uploaded_by_id (FK)  │          │
│ approved_by_id (FK)  │          │
│ test_name            │          │
│ test_type            │          │
│ file (encrypted)     │          │
│ status               │          │
│ uploaded_at          │          │
│ verified_at          │          │
└──────────────────────┘          │
         │                        │
         ▼                        │
┌──────────────────────────────────────────┐
│   reports_reportaccessaudit (NEW)        │
├──────────────────────────────────────────┤
│ id (PK)                                  │
│ report_id (FK) ──────────────────────────┘
│ user_id (FK)                             │
│ access_type (view/download/denied)       │
│ status (success/denied)                  │
│ reason                                   │
│ ip_address                               │
│ accessed_at                              │
│ INDEX: (report_id, -accessed_at)         │
│ INDEX: (user_id, -accessed_at)           │
└──────────────────────────────────────────┘
```

## Encryption Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Encryption Process                           │
└─────────────────────────────────────────────────────────────────┘

UPLOAD:
    ┌──────────────┐
    │ Lab Tech     │
    │ Uploads File │
    └──────┬───────┘
           │
           ▼
    ┌──────────────────────┐
    │ ReportUploadSerializer│
    │ .create()            │
    └──────┬───────────────┘
           │
           ▼
    ┌──────────────────────┐
    │ encrypt_report_bytes │
    │ (file_crypto.py)     │
    └──────┬───────────────┘
           │
           ▼
    ┌──────────────────────┐
    │ Fernet Cipher        │
    │ Key: SHA256(         │
    │   SECRET_KEY +       │
    │   "report-file"      │
    │ )                    │
    └──────┬───────────────┘
           │
           ▼
    ┌──────────────────────┐
    │ Encrypted Bytes      │
    │ + ".enc" extension   │
    └──────┬───────────────┘
           │
           ▼
    ┌──────────────────────┐
    │ Save to Storage      │
    │ (media/reports/)     │
    └──────────────────────┘

DOWNLOAD:
    ┌──────────────┐
    │ User Request │
    │ Download     │
    └──────┬───────┘
           │
           ▼
    ┌──────────────────────┐
    │ Access Control Check │
    │ (ReportAccessValidator)
    └──────┬───────────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
✅ ALLOW    ❌ DENY
    │             │
    │             ▼
    │        ┌──────────────┐
    │        │ Log Denied   │
    │        │ Return 403   │
    │        └──────────────┘
    │
    ▼
┌──────────────────────┐
│ Read Encrypted File  │
│ from Storage         │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ decrypt_report_bytes │
│ (file_crypto.py)     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Fernet Decipher      │
│ (Same Key)           │
└──────┬───────────────┘
       │
   ┌───┴───┐
   │       │
   ▼       ▼
✅ OK  ❌ ERROR
   │       │
   │       ▼
   │  ┌──────────────┐
   │  │ Log Failed   │
   │  │ Return 500   │
   │  └──────────────┘
   │
   ▼
┌──────────────────────┐
│ Log Success Access   │
│ Return Decrypted     │
│ File to User         │
└──────────────────────┘
```

## Role-Based Access Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│                    Access Control Matrix                        │
└─────────────────────────────────────────────────────────────────┘

                    Patient  Lab Tech  Doctor  Admin
                    ───────  ────────  ──────  ─────
View Own Reports      ✅*      ✅        ✅      ✅
View All Reports      ❌       ❌        ✅      ✅
Download Own          ✅*      ✅        ✅      ✅
Download All          ❌       ❌        ✅      ✅
Upload Reports        ❌       ✅        ❌      ✅
Approve Reports       ❌       ❌        ✅      ✅
View Access Logs      ❌       ❌        ❌      ✅
Manage Users          ❌       ❌        ❌      ✅

* Only if status="downloadable"

VALIDATION LOGIC:

Patient:
  ├─ Own Report? ──────────────────┐
  │                                 ├─ YES ──┐
  └─ Status = "downloadable"? ──────┘        │
                                             ▼
                                        ✅ ALLOW

Lab Technician:
  ├─ Uploaded by me? ────────────────┐
  │                                  ├─ YES ──┐
  └─ (No status check)               ┘        │
                                             ▼
                                        ✅ ALLOW

Doctor:
  └─ (No checks) ────────────────────────────┐
                                             ▼
                                        ✅ ALLOW

Admin:
  └─ (No checks) ────────────────────────────┐
                                             ▼
                                        ✅ ALLOW
```

## Audit Trail Example

```
┌─────────────────────────────────────────────────────────────────┐
│                    Audit Log Examples                           │
└─────────────────────────────────────────────────────────────────┘

SUCCESS LOGS:
┌────────────────────────────────────────────────────────────────┐
│ 2026-02-06 10:30:45 | patient1 | download | success | 192.168.1.1
│ 2026-02-06 10:31:12 | doctor1  | download | success | 192.168.1.2
│ 2026-02-06 10:32:00 | labtech1 | download | success | 192.168.1.3
└────────────────────────────────────────────────────────────────┘

DENIED LOGS:
┌────────────────────────────────────────────────────────────────┐
│ 2026-02-06 10:33:15 | patient1 | download | denied   | 192.168.1.1
│   Reason: "Not authorized for this report"
│
│ 2026-02-06 10:34:22 | patient2 | download | denied   | 192.168.1.4
│   Reason: "Report is not downloadable yet"
│
│ 2026-02-06 10:35:30 | labtech2 | download | denied   | 192.168.1.5
│   Reason: "Not authorized for this report"
└────────────────────────────────────────────────────────────────┘

SUSPICIOUS ACTIVITY:
┌────────────────────────────────────────────────────────────────┐
│ IP: 192.168.1.99 - 15 denied attempts in 5 minutes
│ User: unknown_user - Multiple failed access attempts
│ Pattern: Trying to access reports from different patients
│ Action: Review logs, consider blocking IP
└────────────────────────────────────────────────────────────────┘
```

## File Structure

```
reports/
├── access_control.py                    ← NEW: Centralized validation
├── file_crypto.py                       ← Encryption/decryption
├── models.py                            ← MODIFIED: Added audit model
├── views.py                             ← MODIFIED: Enhanced access control
├── admin.py                             ← MODIFIED: Registered models
├── serializers.py
├── urls.py
├── api_urls.py
├── notifications.py
├── management/                          ← NEW: Management commands
│   ├── __init__.py
│   └── commands/
│       ├── __init__.py
│       └── verify_report_encryption.py  ← NEW: Verification command
└── migrations/
    └── 0005_add_access_audit.py         ← NEW: Database migration
```

## Security Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    Security Layers                              │
└─────────────────────────────────────────────────────────────────┘

Layer 1: AUTHENTICATION
    └─ JWT Tokens
    └─ OTP for Patients
    └─ Username/Password for Staff

Layer 2: AUTHORIZATION
    └─ Role-Based Access Control (RBAC)
    └─ Patient Data Isolation
    └─ Status-Based Access

Layer 3: ENCRYPTION
    └─ Fernet (AES-128 CBC + HMAC)
    └─ Automatic on Upload
    └─ Verified on Download

Layer 4: AUDIT TRAIL
    └─ All Access Logged
    └─ IP Address Tracked
    └─ Success/Denied Recorded
    └─ Reason for Denial

Layer 5: MONITORING
    └─ Admin Dashboard
    └─ Search & Filter
    └─ Suspicious Activity Detection
    └─ Management Commands
```

---

**Architecture Version:** 1.0.0
**Last Updated:** 2026-02-06
