# reports/api_urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Upload report (lab technician)
    path("upload/", views.UploadReportView.as_view(), name="upload-report"),
    
    # List reports (patient sees own, doctor sees all)
    path("my-reports/", views.PatientReportsListView.as_view(), name="my-reports"),
    
    # Doctor dashboard - all reports
    path("doctor/all-reports/", views.DoctorReportListView.as_view(), name="doctor-all-reports"),
    
    # Lab assistant dashboard - their uploads
    path("lab-assistant/my-uploads/", views.LabAssistantReportsView.as_view(), name="lab-my-uploads"),
    
    # Mark report as verified/downloadable (doctor)
    path("<int:report_id>/verify/", views.MarkReportVerifiedView.as_view(), name="verify-report"),
    path("<int:report_id>/download/", views.download_report, name="download-report"),
]
