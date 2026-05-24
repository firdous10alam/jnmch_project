# Setup & Deployment Guide

## Quick Start (5 minutes)

### 1. Apply Database Migration
```bash
cd jnmch_project
python manage.py migrate reports
```

### 2. Verify Encryption
```bash
python manage.py verify_report_encryption
```

### 3. Test Access Control
```bash
# Start development server
python manage.py runserver

# In another terminal, test patient access
curl -X POST http://localhost:8000/api/accounts/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"patient1","password":"Patient@123"}'

# Use returned token to test report access
curl -X GET http://localhost:8000/api/reports/my-reports/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. View Access Logs
```
1. Go to http://localhost:8000/admin/
2. Login with superuser credentials
3. Click "Report Access Audits"
4. View all access attempts
```

## Full Deployment Checklist

### Pre-Deployment
- [ ] Backup current database
- [ ] Review SECURITY.md
- [ ] Test in development environment
- [ ] Review access control rules

### Database Migration
```bash
# Backup database
python manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json

# Apply migration
python manage.py migrate reports

# Verify migration
python manage.py showmigrations reports
```

### Verification
```bash
# Check encryption status
python manage.py verify_report_encryption

# If any unencrypted reports found, fix them
python manage.py verify_report_encryption --fix

# Verify all reports are now encrypted
python manage.py verify_report_encryption
```

### Testing

#### Test Patient Access
```bash
# 1. Get patient token
TOKEN=$(curl -s -X POST http://localhost:8000/api/accounts/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"patient1","password":"Patient@123"}' | jq -r '.access')

# 2. View own reports (should work)
curl -X GET http://localhost:8000/api/reports/my-reports/ \
  -H "Authorization: Bearer $TOKEN"

# 3. Try to download unapproved report (should fail)
curl -X GET http://localhost:8000/api/reports/1/download/ \
  -H "Authorization: Bearer $TOKEN"
# Expected: "Report is not downloadable yet"

# 4. Try to access other patient's report (should fail)
curl -X GET http://localhost:8000/api/reports/999/download/ \
  -H "Authorization: Bearer $TOKEN"
# Expected: "Not authorized for this report"
```

#### Test Doctor Access
```bash
# 1. Get doctor token
TOKEN=$(curl -s -X POST http://localhost:8000/api/accounts/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"doctor1","password":"Doctor@123"}' | jq -r '.access')

# 2. View all reports (should work)
curl -X GET http://localhost:8000/api/reports/my-reports/ \
  -H "Authorization: Bearer $TOKEN"

# 3. Approve a report
curl -X POST http://localhost:8000/api/reports/1/mark-downloadable/ \
  -H "Authorization: Bearer $TOKEN"

# 4. Verify patient can now download
# (Use patient token from above)
```

#### Test Lab Technician Access
```bash
# 1. Get lab tech token
TOKEN=$(curl -s -X POST http://localhost:8000/api/accounts/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"labtech1","password":"Lab@123"}' | jq -r '.access')

# 2. View own uploads (should work)
curl -X GET http://localhost:8000/api/reports/my-reports/ \
  -H "Authorization: Bearer $TOKEN"

# 3. Try to access other tech's upload (should fail)
curl -X GET http://localhost:8000/api/reports/999/download/ \
  -H "Authorization: Bearer $TOKEN"
```

### Admin Verification
```bash
# 1. Login to admin panel
# http://localhost:8000/admin/

# 2. Navigate to Reports > Report Access Audits

# 3. Verify:
#    - Access logs exist
#    - Denied attempts are logged
#    - IP addresses are captured
#    - Timestamps are correct
```

### Production Deployment

#### 1. Update Settings
```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')  # Use environment variable
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

#### 2. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

#### 3. Run Migrations
```bash
python manage.py migrate
```

#### 4. Verify Encryption
```bash
python manage.py verify_report_encryption
```

#### 5. Start with Gunicorn
```bash
pip install gunicorn
gunicorn jnmch_project.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

#### 6. Configure Nginx (Example)
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /path/to/staticfiles/;
    }
    
    location /media/ {
        alias /path/to/media/;
    }
}
```

## Monitoring Commands

### Check Encryption Status
```bash
python manage.py verify_report_encryption
```

### View Recent Access Logs
```bash
python manage.py shell
```

```python
from reports.models import ReportAccessAudit
from django.utils import timezone
from datetime import timedelta

# Last 24 hours
recent = ReportAccessAudit.objects.filter(
    accessed_at__gte=timezone.now() - timedelta(days=1)
).order_by('-accessed_at')

for log in recent[:20]:
    print(f"{log.accessed_at} | {log.user} | {log.access_type} | {log.status} | {log.ip_address}")

# Denied accesses
denied = ReportAccessAudit.objects.filter(status='denied').order_by('-accessed_at')[:10]
for log in denied:
    print(f"{log.accessed_at} | {log.user} | DENIED | {log.reason}")

exit()
```

### Check for Suspicious Activity
```bash
python manage.py shell
```

```python
from reports.models import ReportAccessAudit
from django.db.models import Count

# Users with most denied accesses
suspicious = ReportAccessAudit.objects.filter(
    status='denied'
).values('user__username').annotate(
    count=Count('id')
).order_by('-count')[:10]

for item in suspicious:
    print(f"{item['user__username']}: {item['count']} denied attempts")

# IPs with most denied accesses
suspicious_ips = ReportAccessAudit.objects.filter(
    status='denied'
).values('ip_address').annotate(
    count=Count('id')
).order_by('-count')[:10]

for item in suspicious_ips:
    print(f"{item['ip_address']}: {item['count']} denied attempts")

exit()
```

## Troubleshooting

### Migration Fails
```bash
# Check migration status
python manage.py showmigrations reports

# If stuck, rollback previous migration
python manage.py migrate reports 0004_encrypt_existing_report_files

# Then try again
python manage.py migrate reports
```

### Encryption Verification Fails
```bash
# Check which reports are unencrypted
python manage.py verify_report_encryption

# Fix unencrypted reports
python manage.py verify_report_encryption --fix

# Verify again
python manage.py verify_report_encryption
```

### Access Denied Errors
```bash
# Check access logs
python manage.py shell
from reports.models import ReportAccessAudit
logs = ReportAccessAudit.objects.filter(status='denied').order_by('-accessed_at')[:10]
for log in logs:
    print(f"{log.user} - {log.reason}")
exit()
```

### Database Connection Issues
```bash
# Test database connection
python manage.py dbshell

# If fails, check settings.py DATABASES configuration
# Verify MySQL is running and credentials are correct
```

## Rollback Procedure

If you need to rollback:

```bash
# 1. Restore database from backup
mysql -u user -p database < backup_YYYYMMDD_HHMMSS.json

# 2. Rollback migration
python manage.py migrate reports 0004_encrypt_existing_report_files

# 3. Verify
python manage.py showmigrations reports
```

## Performance Optimization

### Database Indexes
Indexes are automatically created by migration:
- `(report, -accessed_at)` - Fast report history
- `(user, -accessed_at)` - Fast user activity

### Query Optimization
```python
# Good - Uses select_related
reports = Report.objects.select_related(
    'patient', 'uploaded_by', 'approved_by'
).all()

# Good - Uses prefetch_related
reports = Report.objects.prefetch_related(
    'access_logs'
).all()

# Bad - N+1 queries
for report in Report.objects.all():
    print(report.patient.user.username)  # Extra query per report
```

## Monitoring Dashboard

Create a custom admin view to monitor:

```python
# In admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import ReportAccessAudit

@admin.register(ReportAccessAudit)
class ReportAccessAuditAdmin(admin.ModelAdmin):
    list_display = ('report', 'user', 'access_type', 'status_badge', 'accessed_at', 'ip_address')
    list_filter = ('access_type', 'status', 'accessed_at')
    search_fields = ('user__username', 'report__test_name', 'ip_address')
    readonly_fields = ('report', 'user', 'access_type', 'status', 'reason', 'ip_address', 'accessed_at')
    
    def status_badge(self, obj):
        if obj.status == 'success':
            color = 'green'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.status.upper()
        )
    status_badge.short_description = 'Status'
```

## Support

For issues or questions:
1. Check SECURITY.md for detailed documentation
2. Review QUICK_REFERENCE.md for common tasks
3. Check access logs in admin panel
4. Run verification command
5. Contact system administrator

---

**Last Updated:** 2026-02-06
**Version:** 1.0.0
