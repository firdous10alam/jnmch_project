# reports/views.py - FIXED VERSION
from rest_framework import generics, permissions, status, serializers
import logging

logger = logging.getLogger(__name__)
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from django.db.models import Q
from django.http import HttpResponse
import mimetypes
import os
from cryptography.fernet import InvalidToken
from .models import Report, ReportAccessAudit
from .serializers import ReportSerializer, ReportUploadSerializer
from .access_control import ReportAccessValidator
from accounts.models import Patient
from .notifications import ReportReadyNotificationService
from .file_crypto import decrypt_report_bytes


class UploadReportView(generics.CreateAPIView):
    serializer_class = ReportUploadSerializer
    queryset = Report.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        if self.request.user.role != "lab_technician":
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only lab technicians can upload reports")
        serializer.save()


class MarkReportVerifiedView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, report_id):
        try:
            report = Report.objects.get(report_id=report_id)
        except Report.DoesNotExist:
            return Response({"error": "Report not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user.role != "doctor":
            return Response({"error": "Only doctors can verify reports"}, status=status.HTTP_403_FORBIDDEN)
        
        if report.status == "downloadable":
            return Response({"error": "Report already verified"}, status=status.HTTP_400_BAD_REQUEST)
        
        report.status = "downloadable"
        report.verified_at = timezone.now()
        report.approved_by = request.user
        report.save()

        notification_sent = ReportReadyNotificationService.notify(report)
        
        serializer = ReportSerializer(report)
        data = serializer.data
        data["notification_sent"] = notification_sent
        return Response(data, status=status.HTTP_200_OK)


class PatientReportsListView(generics.ListAPIView):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.role == "patient":
            try:
                patient = Patient.objects.get(user=user)
                return Report.objects.filter(patient=patient).order_by("-uploaded_at")
            except Patient.DoesNotExist:
                return Report.objects.none()
        
        if user.role == "doctor":
            return Report.objects.all().order_by("-uploaded_at")
        
        if user.role == "lab_technician":
            return Report.objects.filter(uploaded_by=user).order_by("-uploaded_at")
        
        if user.role == "admin":
            return Report.objects.all().order_by("-uploaded_at")
        
        return Report.objects.none()

    def list(self, request, *args, **kwargs):
        user = request.user
        try:
            qs = self.get_queryset()
            count = qs.count() if qs is not None else 0
        except Exception as e:
            logger.exception('Error building queryset for user %s: %s', getattr(user, 'username', None), e)
            return Response({'detail': 'Error fetching reports'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        info_msg = f"PatientReportsListView called by user={getattr(user, 'username', None)} role={getattr(user, 'role', None)} returning_count={count}"
        logger.info(info_msg)
        print(info_msg)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class DoctorReportListView(generics.ListAPIView):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role != "doctor":
            return Report.objects.none()
        return Report.objects.all().prefetch_related('patient', 'uploaded_by').order_by("-uploaded_at")


class LabAssistantReportsView(generics.ListAPIView):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role != "lab_technician":
            return Report.objects.none()
        return Report.objects.filter(uploaded_by=self.request.user).order_by("-uploaded_at")


@api_view(['GET'])
def download_report(request, report_id):
    try:
        report = Report.objects.get(report_id=report_id)
    except Report.DoesNotExist:
        return HttpResponse("Report not found", status=404)

    user = request.user
    role = getattr(user, "role", None)
    
    if role == "patient":
        try:
            patient = Patient.objects.get(user=user)
            if report.patient_id != patient.pk or report.status != "downloadable":
                return HttpResponse("Not authorized", status=403)
        except Patient.DoesNotExist:
            return HttpResponse("Not authorized", status=403)
    elif role not in ["doctor", "admin"]:
        return HttpResponse("Not authorized", status=403)

    try:
        with report.file.open("rb") as f:
            encrypted_bytes = f.read()
        decrypted_bytes = decrypt_report_bytes(encrypted_bytes)
    except Exception as e:
        logger.error(f"Error: {e}")
        return HttpResponse("Error", status=500)

    stored_name = os.path.basename(report.file.name)
    download_name = stored_name.replace(".enc", "")
    
    response = HttpResponse(decrypted_bytes, content_type="application/octet-stream")
    response["Content-Disposition"] = f'attachment; filename="{download_name}"'
    return response
