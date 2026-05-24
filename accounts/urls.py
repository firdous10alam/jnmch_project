# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Frontend views
    path("home/", views.home_page, name="home"),
    path("patient-register/", views.patient_register_page, name="patient_register"),
    path("patient-login/", views.patient_login_page, name="patient_login"),
    path("staff-login/", views.staff_login, name="staff_login"),
    path("patient-request-otp/", views.patient_request_otp, name="patient_request_otp"),
    path("patient-verify-otp/", views.patient_verify_otp, name="patient_verify_otp"),
    path("patient-dashboard/", views.patient_dashboard, name="patient_dashboard"),
    path("doctor-dashboard/", views.doctor_dashboard, name="doctor_dashboard"),
    path("lab-assistant-dashboard/", views.lab_assistant_dashboard, name="lab_assistant_dashboard"),
    path("staff/", views.staff_register_page, name="staff_register"),
]

