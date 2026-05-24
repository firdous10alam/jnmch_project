# accounts/views.py
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.contrib import messages
from .serializers import StaffRegistrationSerializer, PatientRegistrationSerializer, PatientSerializer
from .models import Patient
from .utils import aadhaar_tokenize, encrypt_aadhaar
from django.db import transaction
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

User = get_user_model()


class PatientRegistrationView(APIView):
    """Register a new patient with full details"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        # Collect patient data
        username = request.data.get("username")
        password = request.data.get("password")
        email = request.data.get("email")
        phone = request.data.get("phone")
        aadhaar = request.data.get("aadhaar")
        dob = request.data.get("dob")
        gender = request.data.get("gender")
        first_name = request.data.get("first_name", "")
        last_name = request.data.get("last_name", "")

        # Basic Validation
        logger.debug('PatientRegistration payload: %s', request.data)
        if not all([username, password, email, phone, aadhaar, dob, gender]):
            logger.warning('Missing required registration fields')
            return Response({"error": "All fields required: username, password, email, phone, aadhaar, dob, gender"}, status=status.HTTP_400_BAD_REQUEST)

        # Normalize aadhaar (strip spaces) and validate format loosely
        aadhaar = aadhaar.replace(' ', '')
        if not aadhaar.isdigit() or len(aadhaar) != 12:
            return Response({"error": "Invalid aadhaar value"}, status=status.HTTP_400_BAD_REQUEST)

        # Parse dob to date
        try:
            if isinstance(dob, str):
                dob_date = datetime.fromisoformat(dob).date()
            else:
                dob_date = dob
        except Exception:
            return Response({"error": "Invalid dob format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate gender
        if gender not in ('M', 'F', 'O'):
            return Response({"error": "Invalid gender"}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            logger.warning('Attempt to register with existing username: %s', username)
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        aadhaar_token = aadhaar_tokenize(aadhaar)
        if User.objects.filter(role="patient", aadhaar_token=aadhaar_token).exists():
            logger.warning('Attempt to register with existing aadhaar: %s', aadhaar)
            return Response({"error": "Aadhaar already registered"}, status=status.HTTP_400_BAD_REQUEST)

        # Create User and Patient atomically
        try:
            with transaction.atomic():
                user = User.objects.create(
                    username=username,
                    email=email,
                    phone=phone,
                    aadhaar_token=aadhaar_token,
                    first_name=first_name,
                    last_name=last_name,
                    role='patient'
                )
                user.set_password(password)
                user.save()

                # Create Patient profile (use parsed dob_date)
                patient = Patient.objects.create(
                    user=user,
                    aadhaar=encrypt_aadhaar(aadhaar),
                    dob=dob_date,
                    gender=gender,
                    phone=phone,
                    email=email
                )
                patient.generate_registration_id()
                patient.save()

            # Generate tokens
            refresh = RefreshToken.for_user(user)

            return Response({
                "message": "Patient registered successfully",
                "registration_id": patient.registration_id,
                "username": username,
                "email": email,
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StaffTokenObtainPairView(TokenObtainPairView):
    """
    Allow only doctor / lab_technician / admin to log in here.
    """
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"detail":"No such user"}, status=status.HTTP_401_UNAUTHORIZED)
        if user.role not in ("doctor","lab_technician","admin"):
            return Response({"detail":"Not allowed to login here"}, status=status.HTTP_403_FORBIDDEN)
        
        # Get the response from parent class
        response = super().post(request, *args, **kwargs)
        
        # Add user role to the response for client-side routing
        if response.status_code == 200:
            response.data['role'] = user.role
        
        return response


class PatientTokenObtainPairView(TokenObtainPairView):
    """
    Patient login - by username/password
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"detail":"No such user"}, status=status.HTTP_401_UNAUTHORIZED)
        if user.role != "patient":
            return Response({"detail":"Only patients can login here"}, status=status.HTTP_403_FORBIDDEN)
        return super().post(request, *args, **kwargs)


class PatientInfoView(APIView):
    """
    Get logged-in patient's information
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return Response({"error": "Patient profile not found"}, status=status.HTTP_404_NOT_FOUND)

        # Use serializer for consistent output and safer handling
        serializer = PatientSerializer(patient, context={'request': request})
        data = serializer.data

        # Add a friendly full_name field
        data['full_name'] = request.user.get_full_name() or request.user.username

        return Response(data, status=status.HTTP_200_OK)


class StaffRegistrationView(APIView):
    """
    Register doctor / lab_technician / admin
    """
    permission_classes = [permissions.IsAdminUser]  

    def post(self, request):
        serializer = StaffRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "Staff registered successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Frontend Views

def home_page(request):
    return render(request, 'home.html')

def patient_register_page(request):
    """Patient registration form"""
    return render(request, 'accounts/patient_register.html')

def patient_login_page(request):
    """Patient login form"""
    return render(request, 'accounts/patient_login.html')

def staff_login(request):
    """Staff (doctor/lab_technician) login"""
    return render(request, 'accounts/staff_login.html')

def patient_request_otp(request):
    """OTP request for existing patients"""
    return render(request, 'accounts/patient_request_otp.html')

def patient_verify_otp(request):
    """OTP verification"""
    return render(request, 'accounts/patient_verify_otp.html')

def patient_dashboard(request):
    """Patient dashboard - shows their reports"""
    return render(request, 'accounts/patient_dashboard.html')

def doctor_dashboard(request):
    """Doctor dashboard - shows all reports with patient info"""
    return render(request, 'accounts/doctor_dashboard.html')

def lab_assistant_dashboard(request):
    """Lab assistant dashboard - upload and manage reports"""
    return render(request, 'accounts/lab_assistant_dashboard.html')

def staff_register_page(request):
    """Staff registration page"""
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        if role not in ("doctor", "lab_technician", "admin"):
            messages.error(request, "Invalid role selected")
            return redirect("staff_register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("staff_register")

        user = User.objects.create(
            username=username,
            email=email,
            role=role,
            is_staff=True
        )
        user.set_password(password)
        user.save()
        
        # Create profile
        if role == 'doctor':
            from .models import Doctor
            Doctor.objects.create(user=user)
        elif role == 'lab_technician':
            from .models import LabTechnician
            LabTechnician.objects.create(user=user)

        messages.success(request, "Staff registered successfully")
        return redirect("staff_register")

    return render(request, "staff/register.html")
