# reports/urls.py
from django.urls import path
from . import frontend_views

urlpatterns = [
    path("upload/", frontend_views.upload_report_page, name="upload_report"),
    path("my-reports/", frontend_views.reports_list_page, name="my_reports"),
]
