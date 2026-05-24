# accounts/api_urls.py
from django.urls import path
from .views import (
    StaffTokenObtainPairView,
    PatientTokenObtainPairView,
    PatientRegistrationView,
    PatientInfoView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Patient APIs
    path("patient/register/", PatientRegistrationView.as_view(), name="patient_register"),
    path("patient/login/", PatientTokenObtainPairView.as_view(), name="patient_login"),
    path("patient/info/", PatientInfoView.as_view(), name="patient_info"),
    
    # Staff APIs
    path("staff/login/", StaffTokenObtainPairView.as_view(), name="staff_login"),
    
    # Token refresh
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
