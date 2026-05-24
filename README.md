# JNMCH Online Test Report Portal

A Django-based web application for managing and accessing medical test reports securely with role-based access control and OTP-based patient authentication.

## 📋 Quick Start

### Prerequisites
- Python 3.12+
- MySQL 5.7+
- Git

### Installation Steps

1. **Navigate to project directory**
```bash
cd "c:\Users\khana\Downloads\Project Lab\Lab-Project"
```

2. **Activate virtual environment**
```bash
.\env\Scripts\Activate.ps1    # Windows PowerShell
```

3. **Install dependencies** (if not already installed)
```bash
pip install -r jnmch_project/requirements.txt
```

4. **Navigate to Django project**
```bash
cd jnmch_project
```

5. **Run migrations**
```bash
python manage.py migrate
```

6. **Create superuser** (for admin access)
```bash
python manage.py createsuperuser
# Follow prompts to create admin user
```

7. **Start development server**
```bash
python manage.py runserver
```

8. **Access the application**
```
http://localhost:8000/
```

---

## 👥 User Roles & Access

### 1. **Patient** (role='patient')
- **Login Method**: OTP-based (Aadhaar/UHID)
- **Access**:
  - View their own test reports
  - Request OTP for login
  - View report status
  - Download approved reports
- **Routes**:
  - `/accounts/patient-request-otp/` - Request OTP
  - `/accounts/patient-verify-otp/` - Verify OTP
  - `/accounts/patient-dashboard/` - View reports

### 2. **Doctor** (role='doctor')
- **Login Method**: Username/Password (Staff Token)
- **Access**:
  - View all test reports
  - Approve/mark reports as downloadable
  - View patient information
- **Routes**:
  - `/accounts/staff-login/` - Login
  - `/reports/my-reports/` - View & approve reports

### 3. **Lab Technician** (role='lab_technician')
- **Login Method**: Username/Password (Staff Token)
- **Access**:
  - Upload test reports
  - View pending/approved reports
  - Track uploaded reports
- **Routes**:
  - `/accounts/staff-login/` - Login
  - `/reports/upload/` - Upload reports
  - `/reports/my-reports/` - View reports

### 4. **Admin** (role='admin')
- **Login Method**: Username/Password via `/admin/`
- **Access**:
  - Full Django admin panel
  - Manage all users and reports
  - View system statistics
- **Routes**:
  - `/admin/` - Django Admin

---

## 🔌 API Endpoints

### Authentication APIs
```
POST   /api/accounts/token/
       Body: {"username": "user", "password": "pass"}
       Response: {"access": "jwt_token", "refresh": "refresh_token"}
       
POST   /api/accounts/token/refresh/
       Body: {"refresh": "refresh_token"}
       Response: {"access": "new_jwt_token"}
```

### OTP APIs
```
POST   /api/otp/request/
       Body: {"aadhaar": "aadhaar_number", "phone": "9876543210"}
       Response: {"session_id": "uuid", "message": "OTP sent"}
       
POST   /api/otp/verify/
       Body: {"session_id": "uuid", "otp": "123456"}
       Response: {"access": "jwt_token", "refresh": "refresh_token"} or message
```

### Report APIs
```
POST   /api/reports/upload/
       Headers: Authorization: Bearer <jwt_token>
       Body: FormData {patient, test_name, file}
       Response: {"report_id": ..., "status": "pending"}
       
GET    /api/reports/my-reports/
       Headers: Authorization: Bearer <jwt_token>
       Response: [{report_id, test_name, status, file_url, uploaded_at, ...}]
       
POST   /api/reports/<report_id>/mark-downloadable/
       Headers: Authorization: Bearer <jwt_token>
       Response: {"detail": "report marked downloadable"}
```

---

## 🧪 Test Data Setup

### Create Test Users
```bash
python manage.py shell
```

```python
from accounts.models import User, Patient, Doctor, LabTechnician

# Patient
patient_user = User.objects.create_user(
    username='patient1',
    password='Patient@123',
    first_name='John',
    last_name='Doe',
    email='patient1@example.com',
    phone='9876543210',
    role='patient'
)
Patient.objects.create(
    user=patient_user,
    registration_id='PAT001',
    dob='2000-01-01',
    gender='M'
)

# Doctor
doctor_user = User.objects.create_user(
    username='doctor1',
    password='Doctor@123',
    first_name='Dr.',
    last_name='Smith',
    email='doctor1@example.com',
    phone='9123456789',
    role='doctor'
)
Doctor.objects.create(
    user=doctor_user,
    doctor_reg_no='DOC001',
    specialization='Cardiology'
)

# Lab Technician
lab_user = User.objects.create_user(
    username='labtech1',
    password='Lab@123',
    first_name='Lab',
    last_name='Tech',
    email='labtech1@example.com',
    phone='9988776655',
    role='lab_technician'
)
LabTechnician.objects.create(
    user=lab_user,
    employee_id='LAB001',
    lab_section='Pathology'
)

exit()
```

---

## 📁 File Structure

```
jnmch_project/
├── manage.py                          # Django management CLI
├── requirements.txt                   # Python dependencies
│
├── jnmch_project/                     # Main project package
│   ├── settings.py                    # Core configuration
│   ├── urls.py                        # URL routing
│   ├── wsgi.py                        # WSGI application
│   └── views.py                       # Home view
│
├── accounts/                          # User & Auth management
│   ├── models.py                      # User, Patient, Doctor, LabTechnician
│   ├── views.py                       # API endpoints
│   ├── frontend_views.py              # Template views
│   ├── serializers.py                 # DRF serializers (if any)
│   ├── urls.py                        # Frontend routes
│   ├── api_urls.py                    # API routes
│   └── utils.py                       # Utility functions
│
├── otp/                               # OTP authentication
│   ├── models.py                      # OTPSession model
│   ├── views.py                       # OTP API views
│   └── urls.py                        # OTP routes
│
├── reports/                           # Report management
│   ├── models.py                      # Report model
│   ├── views.py                       # API endpoints
│   ├── frontend_views.py              # Template views
│   ├── serializers.py                 # DRF serializer
│   ├── urls.py                        # Frontend routes
│   └── api_urls.py                    # API routes
│
├── templates/                         # HTML templates
│   ├── base.html                      # Base template
│   ├── home.html                      # Home page
│   ├── accounts/
│   │   ├── staff_login.html
│   │   ├── patient_request_otp.html
│   │   ├── patient_verify_otp.html
│   │   └── patient_dashboard.html
│   └── reports/
│       ├── upload_report.html
│       └── report_list.html
│
├── media/                             # User uploads
├── staticfiles/                       # Collected static files
└── db.sqlite3                         # SQLite database (dev only)
```

---

## 🔒 Security Information

### OTP Flow
- **Request OTP**: Patient provides Aadhaar/UHID
- **Send OTP**: Mock SMS prints to console (2-digit code)
- **Verify OTP**: OTP valid for 5 minutes, max 3 attempts
- **Token Generation**: On successful verification, JWT tokens issued

### CSRF Protection
- All POST requests include CSRF token
- Token retrieved from cookies and passed in headers
- Django middleware validates all mutations

### JWT Token Security
- Access Token: 1 hour validity
- Refresh Token: 7 days validity
- Tokens stored in browser localStorage
- Secure header-based transmission

### Password Security
- Django default password hashing
- Minimum 8 characters required
- Validated against common passwords
- User attribute similarity check

---

## 🐛 Troubleshooting

### Database Connection Error
```
Error: (1045, "Access denied for user 'jnmch_app'@'127.0.0.1'")
```
**Solution**: Check MySQL credentials in `.env` or `settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'jnmch_reports',
        'USER': 'jnmch_app',
        'PASSWORD': 'strong_password',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}
```

### Static Files Not Loading
```bash
python manage.py collectstatic --noinput
```

### OTP Not Appearing
- Check server console output
- SMS mock is enabled by default
- OTP printed: `[MOCK SMS to 9876543210]: Your JNMCH OTP is: XXXXXX`

### Login Token Not Working
- Clear browser localStorage: `localStorage.clear()`
- Refresh page and try again
- Check if token is still valid (1 hour expiry)

### Migration Errors
```bash
# Reset migrations (dev only!)
python manage.py flush
python manage.py migrate
```

---

## 📊 API Testing with cURL

### Test Staff Login
```bash
curl -X POST http://localhost:8000/api/accounts/token/ \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"doctor1\", \"password\": \"Doctor@123\"}"
```

### Test Patient OTP Request
```bash
curl -X POST http://localhost:8000/api/otp/request/ \
  -H "Content-Type: application/json" \
  -d "{\"aadhaar\": \"123456789012\"}"
```

### Test Get My Reports (Authenticated)
```bash
curl -X GET http://localhost:8000/api/reports/my-reports/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🚀 Production Deployment

### Django Settings Changes
```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')  # Use environment variable
```

### Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Run with Gunicorn
```bash
pip install gunicorn
gunicorn jnmch_project.wsgi:application --bind 0.0.0.0:8000
```

### Environment Variables (.env)
```
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
ALLOWED_HOSTS=yourdomain.com
MYSQL_DATABASE=jnmch_reports
MYSQL_USER=jnmch_app
MYSQL_PASSWORD=strong_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
SMS_MOCK=False  # Use real SMS gateway in production
```

---

## 📞 Additional Resources

- **Django Docs**: https://docs.djangoproject.com/en/6.0/
- **Django REST Framework**: https://www.django-rest-framework.org/
- **JWT Documentation**: https://github.com/jpadilla/pyjwt
- **Bootstrap**: https://getbootstrap.com/

---

## 📝 License

This project is confidential and proprietary.

---

**Version**: 1.0.0  
**Last Updated**: February 6, 2026  
**Status**: ✅ Ready for Development & Testing
#   j m n c h _ p r o j e c t  
 "# jmnch_project" 
"# jmnch_project" 
