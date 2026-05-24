# reports/access_control.py
from accounts.models import Patient
from .models import Report, ReportAccessAudit


class ReportAccessValidator:
    """Centralized access control validation for reports."""
    
    @staticmethod
    def can_patient_access(user, report):
        """Check if patient can access their own report."""
        if not hasattr(user, 'patient_profile'):
            try:
                patient = Patient.objects.get(user=user)
            except Patient.DoesNotExist:
                return False, "Patient profile not found"
        else:
            patient = user.patient_profile
        
        if report.patient_id != patient.pk:
            return False, "Not authorized for this report"
        
        if report.status != "downloadable":
            return False, "Report is not downloadable yet"
        
        return True, None
    
    @staticmethod
    def can_lab_technician_access(user, report):
        """Check if lab technician can access their uploaded report."""
        if report.uploaded_by_id != user.id:
            return False, "Not authorized for this report"
        return True, None
    
    @staticmethod
    def can_doctor_access(user, report):
        """Doctors can access all reports."""
        return True, None
    
    @staticmethod
    def can_admin_access(user, report):
        """Admins can access all reports."""
        return True, None
    
    @staticmethod
    def validate_access(user, report):
        """Validate user access based on role."""
        role = getattr(user, "role", None)
        
        if role == "patient":
            return ReportAccessValidator.can_patient_access(user, report)
        elif role == "lab_technician":
            return ReportAccessValidator.can_lab_technician_access(user, report)
        elif role == "doctor":
            return ReportAccessValidator.can_doctor_access(user, report)
        elif role == "admin":
            return ReportAccessValidator.can_admin_access(user, report)
        else:
            return False, "Invalid user role"
    
    @staticmethod
    def log_access(report, user, access_type, status, reason=None, ip_address=None):
        """Log report access attempt."""
        ReportAccessAudit.objects.create(
            report=report,
            user=user,
            access_type=access_type,
            status=status,
            reason=reason,
            ip_address=ip_address
        )
