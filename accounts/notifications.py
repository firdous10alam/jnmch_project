import logging
import os

from django.conf import settings


logger = logging.getLogger(__name__)


class SMSNotificationService:
    """Small wrapper for SMS delivery with Twilio + mock fallback."""

    @staticmethod
    def _send_sms_mock(phone, text):
        print(f"[MOCK SMS to {phone}]: {text}")

    @classmethod
    def send(cls, phone, text):
        if not phone:
            logger.warning("SMS skipped: phone number missing")
            return False

        if getattr(settings, "SMS_MOCK", True):
            cls._send_sms_mock(phone, text)
            return True

        sid = getattr(settings, "TWILIO_ACCOUNT_SID", None) or os.getenv("TWILIO_ACCOUNT_SID")
        token = getattr(settings, "TWILIO_AUTH_TOKEN", None) or os.getenv("TWILIO_AUTH_TOKEN")
        from_number = getattr(settings, "TWILIO_FROM_NUMBER", None) or os.getenv("TWILIO_FROM_NUMBER")

        if not (sid and token and from_number):
            logger.warning("Twilio credentials missing, using SMS mock fallback")
            cls._send_sms_mock(phone, text)
            return False

        try:
            from twilio.rest import Client

            client = Client(sid, token)
            client.messages.create(body=text, from_=from_number, to=phone)
            return True
        except Exception:
            logger.exception("Twilio send failed, using SMS mock fallback")
            cls._send_sms_mock(phone, text)
            return False
