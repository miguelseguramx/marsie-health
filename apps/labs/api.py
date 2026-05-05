import hashlib
import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.emails import send_onboarding_email
from apps.accounts.models import OnboardingToken
from apps.accounts.roles import Role, assign_role, user_role
from apps.labs.models import LabReport
from apps.labs.s3 import upload_report_pdf
from apps.patients.models import Patient

ONBOARDING_TOKEN_TTL = timedelta(days=7)


class LabAdminUploadReportSerializer(serializers.Serializer):
    patient_email = serializers.EmailField()
    patient_first_name = serializers.CharField(max_length=150)
    patient_last_name = serializers.CharField(max_length=150)
    file = serializers.FileField()


class LabAdminUploadReportView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        if user_role(request.user) != Role.LAB_ADMIN:
            return Response(
                {"detail": "Only lab admins can upload reports."},
                status=status.HTTP_403_FORBIDDEN,
            )

        membership = request.user.lab_memberships.select_related("lab").first()
        if membership is None:
            return Response(
                {"detail": "You are not a lab admin of any lab."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = LabAdminUploadReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        body = data["file"].read()
        sha256_hex = hashlib.sha256(body).hexdigest()

        existing = LabReport.objects.filter(
            lab=membership.lab, content_hash=sha256_hex
        ).first()
        if existing is not None:
            return Response(
                {
                    "report_id": str(existing.id),
                    "patient_email": existing.patient.user.email,
                    "email_sent": False,
                    "duplicate": True,
                },
                status=status.HTTP_200_OK,
            )

        with transaction.atomic():
            user, _ = self._get_or_create_patient_user(
                email=data["patient_email"],
                first_name=data["patient_first_name"],
                last_name=data["patient_last_name"],
            )
            report = LabReport.objects.create(
                lab=membership.lab,
                patient=user.patient,
                report_type=LabReport.ReportType.CBC,
                raw_pdf_bucket="",
                raw_pdf_s3_key="",
                content_hash=sha256_hex,
                uploaded_by=request.user,
            )
            bucket, key, _ = upload_report_pdf(
                body, lab_slug=membership.lab.slug, report_id=str(report.id)
            )
            report.raw_pdf_bucket = bucket
            report.raw_pdf_s3_key = key
            report.save(update_fields=["raw_pdf_bucket", "raw_pdf_s3_key"])

            email_sent = False
            if not user.has_usable_password():
                token = OnboardingToken.objects.create(
                    token=secrets.token_urlsafe(32),
                    user=user,
                    report=report,
                    expires_at=timezone.now() + ONBOARDING_TOKEN_TTL,
                )
                send_onboarding_email(user, token.token)
                email_sent = True

        return Response(
            {
                "report_id": str(report.id),
                "patient_email": user.email,
                "email_sent": email_sent,
                "duplicate": False,
            },
            status=status.HTTP_201_CREATED,
        )

    def _get_or_create_patient_user(self, *, email: str, first_name: str, last_name: str):
        User = get_user_model()
        user = User.objects.filter(email__iexact=email).first()
        if user is not None:
            return user, False
        user = User(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        user.set_unusable_password()
        user.save()
        assign_role(user, Role.PATIENT)
        Patient.objects.create(user=user)
        return user, True
