# serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Patient, Doctor, LabTechnician
from .utils import aadhaar_tokenize, decrypt_aadhaar, encrypt_aadhaar

User = get_user_model()


class PatientRegistrationSerializer(serializers.ModelSerializer):
    """Register a new patient with basic info"""
    password = serializers.CharField(write_only=True, min_length=8)
    phone = serializers.CharField(max_length=20, required=True)
    email = serializers.EmailField(required=True)
    aadhaar = serializers.CharField(max_length=64, required=True)
    dob = serializers.DateField(required=True)
    gender = serializers.ChoiceField(choices=['M', 'F', 'O'], required=True)
    
    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'phone']
    
    def create(self, validated_data):
        # Extract additional patient info
        aadhaar = self.context.get('aadhaar')
        dob = self.context.get('dob')
        gender = self.context.get('gender')
        phone = validated_data.get('phone')
        email = validated_data.get('email')
        
        password = validated_data.pop("password", None)
        
        # Create User
        user = User(
            username=validated_data.get('username'),
            email=email,
            phone=phone,
            aadhaar_token=aadhaar_tokenize(aadhaar) if aadhaar else None,
            role='patient'
        )
        if password:
            user.set_password(password)
        user.save()
        
        # Create Patient profile
        patient = Patient.objects.create(
            user=user,
            aadhaar=encrypt_aadhaar(aadhaar) if aadhaar else None,
            dob=dob,
            gender=gender,
            phone=phone,
            email=email
        )
        patient.generate_registration_id()
        patient.save()
        
        return user


class PatientSerializer(serializers.ModelSerializer):
    """Full patient info serializer"""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username')
    email = serializers.CharField(source='user.email')
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    aadhaar = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Patient
        fields = ['user_id', 'username', 'email', 'first_name', 'last_name', 
                  'registration_id', 'uhid', 'aadhaar', 'dob', 'gender', 'phone', 'created_at']
        read_only_fields = ['user_id', 'registration_id', 'created_at']

    def get_aadhaar(self, obj):
        plain = decrypt_aadhaar(obj.aadhaar)
        if not plain:
            return None
        if len(plain) <= 4:
            return "****"
        return ("*" * (len(plain) - 4)) + plain[-4:]


class StaffRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "email",
            "role"
        ]

    def validate_role(self, value):
        allowed_roles = ("doctor", "lab_technician", "admin")
        if value not in allowed_roles:
            raise serializers.ValidationError("Invalid staff role")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)  # 🔐 hashing
        user.is_staff = True         # Django permission flag
        user.save()
        
        # Create profile based on role
        if user.role == 'doctor':
            Doctor.objects.create(user=user)
        elif user.role == 'lab_technician':
            LabTechnician.objects.create(user=user)
        
        return user
