import uuid

from django.conf import settings
from django.db import models


class Patient(models.Model):
    SEX_CHOICES = [("M", "M"), ("F", "F"), ("O", "O")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient",
    )
    filaxis_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        null=True,
        blank=True,
    )
    date_of_birth = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Patient<{self.user.email}>"
