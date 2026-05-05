import uuid

from django.conf import settings
from django.db import models


class Lab(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    contact_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class LabAdminMembership(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lab_memberships",
    )
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE, related_name="admins")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "lab")]

    def __str__(self) -> str:
        return f"{self.user} @ {self.lab}"


class LabReport(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "received", "Received"
        PROCESSING = "processing", "Processing"
        PROCESSED = "processed", "Processed"
        FAILED = "failed", "Failed"

    class ReportType(models.TextChoices):
        CBC = "cbc", "Complete Blood Count"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lab = models.ForeignKey(Lab, on_delete=models.PROTECT, related_name="reports")
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="lab_reports",
    )
    report_type = models.CharField(
        max_length=16, choices=ReportType.choices, default=ReportType.CBC
    )
    raw_pdf_bucket = models.CharField(max_length=128)
    raw_pdf_s3_key = models.CharField(max_length=512, db_index=True)
    content_hash = models.CharField(max_length=64, db_index=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.RECEIVED)
    pipeline_version = models.CharField(max_length=32, blank=True)
    raw_payload = models.JSONField(null=True, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_reports",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("lab", "content_hash")]

    def __str__(self) -> str:
        return f"LabReport<{self.lab.slug}/{self.content_hash[:8]}>"
