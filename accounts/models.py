# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid

class User(AbstractUser):
    ROLE_CHOICES = [
        ("patient", "Patient"),
        ("doctor", "Doctor"),
        ("lab_technician", "Lab Technician"),
        ("admin", "Admin"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True, null=True)
    aadhaar_token = models.BinaryField(blank=True, null=True)
    uhid = models.CharField(max_length=128, blank=True, null=True, unique=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='patient_profile')
    registration_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    uhid = models.CharField(max_length=128, unique=True, null=True, blank=True)  # Unique health ID
    aadhaar = models.TextField(null=True, blank=True)  # Encrypted Aadhaar at rest
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def generate_registration_id(self):
        """Generate unique registration ID"""
        if not self.registration_id:
            self.registration_id = f"REG-{uuid.uuid4().hex[:8].upper()}"
        return self.registration_id
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} (Reg: {self.registration_id})"


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='doctor_profile')
    doctor_reg_no = models.CharField(max_length=64, unique=True, null=True, blank=True)
    specialization = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username}"


class LabTechnician(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='labtechnician_profile')
    employee_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    lab_section = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return f"Lab Tech: {self.user.get_full_name() or self.user.username}"



