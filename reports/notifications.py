import logging

from accounts.notifications import SMSNotificationService


logger = logging.getLogger(__name__)


class ReportReadyNotificationService:
    """Sends patient SMS when a report becomes downloadable."""

    @staticmethod
    def _patient_phone(report):
        if getattr(report.patient, "phone", None):
            return report.patient.phone
        if getattr(report.patient, "user", None) and getattr(report.patient.user, "phone", None):
            return report.patient.user.phone
        return None

    @classmethod
    def notify(cls, report):
        phone = cls._patient_phone(report)
        if not phone:
            logger.warning("Report ready SMS skipped: no patient phone for report_id=%s", report.report_id)
            return False

        message = (
            f"Your report is ready for download. Test: {report.test_name}. "
            f"Report ID: {report.report_id}."
        )
        return SMSNotificationService.send(phone, message)
