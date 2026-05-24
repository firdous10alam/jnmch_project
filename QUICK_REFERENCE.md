# Quick Reference: Report Security

## What Changed?

### ✅ Reports are Encrypted
- Files encrypted with Fernet (AES-128)
- Encryption happens automatically on upload
- Decryption only on authorized download

### ✅ Access Control Enforced
- Patients can only access their own reports
- Lab techs can only access their uploads
- Doctors can access all reports
- All access logged with IP address

### ✅ Audit Trail
- Every access attempt logged
- Success and denied attempts tracked
- Viewable in Django admin

## For Developers

### Check Access Control
```python
from reports.access_control import ReportAccessValidator

# Validate access
authorized, error_msg = ReportAccessValidator.validate_access(user, report)
if not authorized:
    return Response({"error": error_msg}, status=403)
```

### Log Access
```python
ReportAccessValidator.log_access(
    report=report,
    user=user,
    access_type="download",
    status="success",
    ip_address=ip
)
```

### Query Access Logs
```python
from reports.models import ReportAccessAudit

# Recent denied accesses
denied = ReportAccessAudit.objects.filter(status="denied").order_by("-accessed_at")[:10]

# User's access history
user_accesses = ReportAccessAudit.objects.filter(user=user).order_by("-accessed_at")

# Report access history
report_accesses = ReportAccessAudit.objects.filter(report=report).order_by("-accessed_at")
```

## For Admins

### View Access Logs
1. Go to `/admin/`
2. Click "Report Access Audits"
3. Filter by:
   - Access type (view, download, denied)
   - Status (success, denied)
   - Date range
4. Search by username, test name, or IP

### Verify Encryption
```bash
python manage.py verify_report_encryption
```

### Fix Unencrypted Reports
```bash
python manage.py verify_report_encryption --fix
```

## For Patients

### What Can I Access?
- ✅ My own reports (after doctor approval)
- ✅ Download approved reports
- ❌ Other patients' reports
- ❌ Unapproved reports

### Why Can't I Download?
- Report not yet approved by doctor
- Report belongs to different patient
- System error (contact admin)

## For Doctors

### What Can I Access?
- ✅ All reports in system
- ✅ Patient information
- ✅ Approve/mark reports downloadable
- ✅ View access logs

### How to Approve?
1. View report in dashboard
2. Click "Approve" or "Mark Downloadable"
3. Patient receives notification
4. Patient can now download

## For Lab Technicians

### What Can I Access?
- ✅ Reports I uploaded
- ✅ Upload new reports
- ❌ Other technicians' uploads
- ❌ Patient reports before upload

### Upload Process
1. Select patient (by Registration ID or UHID)
2. Select test type
3. Upload file
4. File automatically encrypted
5. Doctor reviews and approves

## Security Rules

| Action | Patient | Lab Tech | Doctor | Admin |
|--------|---------|----------|--------|-------|
| View own reports | ✅ | - | - | - |
| View all reports | ❌ | ❌ | ✅ | ✅ |
| Download own reports | ✅* | ✅ | ✅ | ✅ |
| Upload reports | ❌ | ✅ | ❌ | ✅ |
| Approve reports | ❌ | ❌ | ✅ | ✅ |
| View access logs | ❌ | ❌ | ❌ | ✅ |

*Only if status="downloadable"

## Files to Know

| File | Purpose |
|------|---------|
| `reports/access_control.py` | Access validation logic |
| `reports/file_crypto.py` | Encryption/decryption |
| `reports/models.py` | Report & ReportAccessAudit models |
| `reports/views.py` | API endpoints with access control |
| `reports/admin.py` | Admin interface |
| `SECURITY.md` | Full security documentation |

## Common Issues

### "Not authorized for this report"
- Patient: Report belongs to different patient
- Lab Tech: You didn't upload this report
- Solution: Check report ownership in admin

### "Report is not downloadable yet"
- Doctor hasn't approved yet
- Solution: Ask doctor to approve

### "Stored file is unreadable"
- File corruption or encryption issue
- Solution: Run `python manage.py verify_report_encryption`

## Testing Access Control

```bash
# Login as patient
curl -X POST http://localhost:8000/api/accounts/token/ \
  -d '{"username":"patient1","password":"Patient@123"}'

# Try to access own report (should work)
curl -X GET http://localhost:8000/api/reports/1/download/ \
  -H "Authorization: Bearer TOKEN"

# Try to access other patient's report (should fail)
curl -X GET http://localhost:8000/api/reports/999/download/ \
  -H "Authorization: Bearer TOKEN"
```

## Deployment Checklist

- [ ] Run migrations: `python manage.py migrate`
- [ ] Verify encryption: `python manage.py verify_report_encryption`
- [ ] Test patient access (own reports only)
- [ ] Test doctor access (all reports)
- [ ] Check admin panel for access logs
- [ ] Review SECURITY.md for production settings
- [ ] Enable HTTPS
- [ ] Set DEBUG=False
- [ ] Configure SECRET_KEY

## Support

For security issues or questions:
1. Check SECURITY.md for detailed documentation
2. Review access logs in admin panel
3. Run verification command
4. Contact system administrator
