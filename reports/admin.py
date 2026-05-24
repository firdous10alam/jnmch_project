from django.contrib import admin
from .models import Report, ReportAccessAudit

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'test_name', 'patient', 'status', 'uploaded_at')
    list_filter = ('status', 'uploaded_at', 'is_critical')
    search_fields = ('test_name', 'patient__user__username')
    readonly_fields = ('report_id', 'uploaded_at', 'verified_at')

@admin.register(ReportAccessAudit)
class ReportAccessAuditAdmin(admin.ModelAdmin):
    list_display = ('report', 'user', 'access_type', 'status', 'accessed_at', 'ip_address')
    list_filter = ('access_type', 'status', 'accessed_at')
    search_fields = ('user__username', 'report__test_name', 'ip_address')
    readonly_fields = ('report', 'user', 'access_type', 'status', 'reason', 'ip_address', 'accessed_at')

