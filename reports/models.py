# reports/models.py
from django.db import models
from accounts.models import Patient, User
from django.utils import timezone

class Report(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("verified", "Verified"),
        ("downloadable", "Downloadable"),
        ("rejected", "Rejected")
    ]
    
    report_id = models.BigAutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="reports")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="uploads")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approvals")
    test_name = models.CharField(max_length=200)
    test_type = models.CharField(max_length=100, blank=True, null=True)  # e.g., Blood, Urine, X-ray
    file = models.FileField(upload_to="reports/%Y/%m/")
    is_critical = models.BooleanField(default=False)
    visibility = models.CharField(max_length=32, default="private")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    comments = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ["-uploaded_at"]
    
    def __str__(self):
        return f"{self.test_name} - {self.patient} ({self.status})"


class ReportAccessAudit(models.Model):
    """Audit log for all report access attempts."""
    ACCESS_TYPES = [
        ("view", "View"),
        ("download", "Download"),
        ("denied", "Access Denied"),
    ]
    
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="access_logs")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="report_accesses")
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPES)
    status = models.CharField(max_length=20, choices=[("success", "Success"), ("denied", "Denied")])
    reason = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    accessed_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ["-accessed_at"]
        indexes = [
            models.Index(fields=["report", "-accessed_at"]),
            models.Index(fields=["user", "-accessed_at"]),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.access_type} - {self.status} ({self.accessed_at})"
