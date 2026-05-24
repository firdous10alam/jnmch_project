# JNMCH Report Security Implementation

## Overview
This document outlines the security measures implemented for protecting medical test reports in the JNMCH Online Test Report Portal.

## 1. Report Encryption

### Implementation
- **Algorithm**: Fernet (AES-128 in CBC mode with HMAC authentication)
- **Key Derivation**: SHA-256 hash of Django SECRET_KEY + "report-file"
- **Location**: `reports/file_crypto.py`

### Encryption Flow
```
1. Lab technician uploads report file
2. File content is encrypted using encrypt_report_bytes()
3. Encrypted file saved with .enc extension
4. Original unencrypted file never stored on disk
```

### Decryption Flow
```
1. Authorized user requests report download
2. Access control validation performed
3. Encrypted file read from storage
4. File decrypted using decrypt_report_bytes()
5. Decrypted content sent to user
6. Access logged to ReportAccessAudit
```

## 2. Access Control

### Role-Based Access

#### Patient (role='patient')
- Can only view/download their own reports
- Only if report status is "downloadable"
- Validated via Patient.user relationship

#### Lab Technician (role='lab_technician')
- Can view/download reports they uploaded
- Can upload new reports
- Cannot access other technicians' uploads

#### Doctor (role='doctor')
- Can view all reports
- Can approve/mark reports as downloadable
- Full access for clinical review

#### Admin (role='admin')
- Full system access
- Can view all reports and access logs

### Access Validation
Located in `reports/access_control.py`:
- `ReportAccessValidator.validate_access()` - Main validation method
- Role-specific validation methods for each user type
- Centralized logic prevents access control bypasses

## 3. Access Audit Logging

### ReportAccessAudit Model
Tracks all report access attempts with:
- **report**: Foreign key to Report
- **user**: User attempting access
- **access_type**: "view", "download", or "denied"
- **status**: "success" or "denied"
- **reason**: Why access was denied (if applicable)
- **ip_address**: Client IP address
- **accessed_at**: Timestamp

### Indexes
- `(report, -accessed_at)` - Query reports by access history
- `(user, -accessed_at)` - Query user access patterns

### Admin Interface
Access logs visible in Django admin at `/admin/reports/reportaccessaudit/`

## 4. Security Best Practices

### Patient Data Protection
```python
# Patient can only access their own reports
if user.role == "patient":
    patient = Patient.objects.get(user=user)
    if report.patient_id != patient.pk:
        return False, "Not authorized"
```

### Status-Based Access
```python
# Patients can only download "downloadable" reports
if report.status != "downloadable":
    return False, "Report is not downloadable yet"
```

### Decryption Validation
```python
try:
    decrypted = decrypt_report_bytes(encrypted_bytes)
except InvalidToken:
    # Log failed decryption attempt
    ReportAccessValidator.log_access(
        report, user, "download", "denied", "Decryption failed", ip
    )
```

## 5. Management Commands

### Verify Encryption Status
```bash
python manage.py verify_report_encryption
```

Checks all reports for:
- Encryption status
- Decryption integrity
- Corrupted files

**With --fix flag:**
```bash
python manage.py verify_report_encryption --fix
```
Automatically encrypts any unencrypted reports.

## 6. Deployment Checklist

- [ ] Set strong `SECRET_KEY` in production settings
- [ ] Enable HTTPS for all connections
- [ ] Configure secure file storage (S3, etc.)
- [ ] Enable Django CSRF protection
- [ ] Set `DEBUG = False` in production
- [ ] Configure allowed hosts
- [ ] Run migrations: `python manage.py migrate`
- [ ] Verify encryption: `python manage.py verify_report_encryption`
- [ ] Review access logs regularly in admin panel

## 7. Troubleshooting

### "Report is not downloadable yet"
- Doctor must approve report first
- Report status must be "downloadable"
- Check admin panel for report status

### "Not authorized for this report"
- Patient: Verify report belongs to your account
- Lab Tech: Verify you uploaded the report
- Check access logs for denied attempts

### "Stored file is unreadable"
- Report file may be corrupted
- Run: `python manage.py verify_report_encryption`
- Contact system administrator

## 8. Monitoring

### Key Metrics to Monitor
1. Failed access attempts (ReportAccessAudit with status="denied")
2. Decryption failures
3. Unauthorized access patterns
4. Access from unusual IP addresses

### Admin Dashboard Query
```python
# Recent denied accesses
ReportAccessAudit.objects.filter(
    status="denied"
).order_by("-accessed_at")[:50]

# User access history
ReportAccessAudit.objects.filter(
    user=user
).order_by("-accessed_at")
```

## 9. Compliance

This implementation provides:
- ✅ Data encryption at rest (Fernet)
- ✅ Role-based access control (RBAC)
- ✅ Audit logging of all access
- ✅ Patient data isolation
- ✅ Secure authentication (JWT tokens)
- ✅ CSRF protection

Suitable for healthcare data protection requirements.
