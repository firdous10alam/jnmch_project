# otp/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from .models import OTPSession
from accounts.utils import aadhaar_tokenize, otp_hash, verify_otp_hash
from accounts.models import User, Patient
from accounts.notifications import SMSNotificationService
import random
import logging

logger = logging.getLogger(__name__)

class RequestOTPView(APIView):
    permission_classes = []  # open endpoint

    def post(self, request):
        aadhaar = request.data.get("aadhaar")
        registration_id = request.data.get("registration_id")
        
        if not (aadhaar or registration_id):
            return Response(
                {"error": "Aadhaar or Registration ID required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        patient = None
        phone_number = None
        
        # Try to find patient by registration_id first (normalize and case-insensitive)
        if registration_id:
            registration_id = registration_id.strip().upper()
            patient = Patient.objects.filter(registration_id=registration_id).first()
            if not patient:
                logger.debug('No patient found for registration_id=%s', registration_id)
                return Response({"error": "No patient found with this Registration ID"}, status=status.HTTP_404_NOT_FOUND)
        
        # Try to find patient by Aadhaar (tokenized lookup; raw Aadhaar is never stored)
        elif aadhaar:
            # Normalize aadhaar and resolve via token on User
            aadhaar = aadhaar.replace(' ', '')
            if not aadhaar.isdigit() or len(aadhaar) != 12:
                return Response(
                    {"error": "Invalid Aadhaar number. Enter 12 digits."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            aadhaar_token = aadhaar_tokenize(aadhaar)
            user = User.objects.filter(role="patient", aadhaar_token=aadhaar_token).first()
            if user and hasattr(user, 'patient_profile'):
                patient = user.patient_profile
            if not patient:
                logger.debug('No patient found for aadhaar=%s', aadhaar)
                return Response({"error": "No patient found with this Aadhaar number"}, status=status.HTTP_404_NOT_FOUND)
        
        if not patient:
            return Response(
                {"error": "Patient not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get phone number from patient record
        if patient.phone:
            phone_number = patient.phone
        elif hasattr(patient, 'user') and patient.user.phone:
            phone_number = patient.user.phone
        
        if not phone_number:
            return Response(
                {"error": "No phone number registered for this patient"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate OTP
        otp = f"{random.randint(100000, 999999)}"
        hashed_otp = otp_hash(otp)
        expires_at = timezone.now() + timedelta(minutes=5)
        
        # Create OTP session
        session = OTPSession.objects.create(
            user=patient.user if hasattr(patient, 'user') else None,
            aadhaar_token=aadhaar_tokenize(aadhaar) if aadhaar else None,
            phone=phone_number,
            otp_hash=hashed_otp,
            expires_at=expires_at
        )
        
        # Send OTP to registered phone number
        message = f"Your JNMCH OTP for login is: {otp}. Valid for 5 minutes."
        SMSNotificationService.send(phone_number, message)
        
        return Response({
            "session_id": str(session.id),
            "message": "OTP sent to registered mobile number"
        }, status=status.HTTP_200_OK)

class VerifyOTPView(APIView):
    permission_classes = []

    def post(self, request):
        session_id = request.data.get("session_id")
        otp = request.data.get("otp")
        
        if not session_id or not otp:
            return Response(
                {"error": "Session ID and OTP required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            session = OTPSession.objects.get(id=session_id)
        except OTPSession.DoesNotExist:
            return Response(
                {"error": "Invalid session"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if session.used:
            return Response(
                {"error": "OTP already used"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if session.is_expired():
            return Response(
                {"error": "OTP expired"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if verify_otp_hash(otp, session.otp_hash):
            session.used = True
            session.save()
            
            # Check if user exists
            if session.user:
                from rest_framework_simplejwt.tokens import RefreshToken
                refresh = RefreshToken.for_user(session.user)
                
                return Response({
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user_id": session.user.id,
                    "message": "Login successful"
                }, status=status.HTTP_200_OK)
            else:
                # No user exists - registration required
                return Response({
                    "message": "OTP verified. No patient account found. Registration required.",
                    "verified": True
                }, status=status.HTTP_200_OK)
        else:
            session.attempts += 1
            session.save()
            
            if session.attempts >= 3:
                session.used = True
                session.save()
                return Response(
                    {"error": "Too many failed attempts. OTP blocked."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(
                {"error": "Invalid OTP"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
