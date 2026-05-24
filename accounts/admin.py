# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Patient, Doctor, LabTechnician
# from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "first_name", "last_name", "email", "role", "is_active")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Additional", {"fields": ("role","phone","aadhaar_token","uhid")}),
    )

admin.site.register(Patient)
admin.site.register(Doctor)
admin.site.register(LabTechnician)
# admin.site.register(User)