# reports/serializers.py
from rest_framework import serializers
from django.db.models import Q
from django.core.files.base import ContentFile
from .models import Report
from accounts.models import Patient
from .file_crypto import encrypt_report_bytes

class ReportSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    patient_registration_id = serializers.CharField(source='patient.registration_id', read_only=True)
    patient_uhid = serializers.CharField(source='patient.uhid', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    download_url = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'report_id', 'patient', 'patient_name', 'patient_registration_id', 'patient_uhid',
            'uploaded_by', 'uploaded_by_name', 'test_name', 'test_type',
            'is_critical', 'visibility', 'status', 'comments', 'uploaded_at', 
            'verified_at', 'approved_by', 'approved_by_name', 'download_url'
        ]
        read_only_fields = ['uploaded_by', 'status', 'uploaded_at', 'verified_at', 'approved_by']

    def get_download_url(self, obj):
        if obj.status != "downloadable":
            return None
        request = self.context.get("request")
        relative = f"/api/reports/{obj.report_id}/download/"
        return request.build_absolute_uri(relative) if request else relative


class ReportUploadSerializer(serializers.ModelSerializer):
    """Simplified serializer for upload by lab technician"""
    registration_id = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = Report
        fields = ['registration_id', 'test_name', 'test_type', 'file', 'is_critical', 'comments']
        extra_kwargs = {
            'test_name': {'required': True},
            'file': {'required': True},
            'is_critical': {'required': False},
            'test_type': {'required': False, 'allow_blank': True},
            'comments': {'required': False, 'allow_blank': True},
        }
    
    def validate(self, attrs):
        """Validate the combined data"""
        registration_id = attrs.get('registration_id', '').strip()
        
        if not registration_id:
            raise serializers.ValidationError({"registration_id": "Registration ID is required"})
        
        # Find patient
        patient = Patient.objects.filter(
            Q(registration_id=registration_id) | Q(uhid=registration_id)
        ).first()
        
        if not patient:
            raise serializers.ValidationError({
                "registration_id": f"Patient not found with this Registration ID or UHID: '{registration_id}'"
            })
        
        # Store patient for create method
        attrs['_patient'] = patient
        return attrs
    
    def create(self, validated_data):
        patient = validated_data.pop('_patient')
        registration_id = validated_data.pop('registration_id')
        uploaded_file = validated_data.pop('file')
        encrypted_content = encrypt_report_bytes(uploaded_file.read())
        encrypted_name = f"{uploaded_file.name}.enc"
        
        # Create report
        report = Report(
            patient=patient,
            uploaded_by=self.context['request'].user,
            status="pending",
            **validated_data
        )
        report.file.save(encrypted_name, ContentFile(encrypted_content), save=False)
        report.save()
        return report
