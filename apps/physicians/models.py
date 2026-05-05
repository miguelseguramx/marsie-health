import uuid

from django.conf import settings
from django.db import models


class Physician(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="physician",
    )
    license_number = models.CharField(max_length=64, unique=True, null=True, blank=True)
    specialty = models.CharField(max_length=128, blank=True)
    patients = models.ManyToManyField(
        "patients.Patient",
        through="CareRelationship",
        related_name="physicians",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Physician<{self.user.email}>"


class CareRelationship(models.Model):
    physician = models.ForeignKey(
        Physician,
        on_delete=models.CASCADE,
        related_name="care_relationships",
    )
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="care_relationships",
    )
    consent_flag = models.BooleanField(default=False)
    consent_recorded_at = models.DateTimeField(null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("physician", "patient", "start_date")]

    def __str__(self) -> str:
        return f"CareRelationship<{self.physician_id} ↔ {self.patient_id}>"
