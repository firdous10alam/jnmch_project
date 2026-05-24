# otp/models.py
from django.db import models
import uuid
from django.utils import timezone

class OTPSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)
    aadhaar_token = models.BinaryField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    otp_hash = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    used = models.BooleanField(default=False)
    request_ip = models.CharField(max_length=45, null=True, blank=True)

    def is_expired(self):
        return timezone.now() > self.expires_at
