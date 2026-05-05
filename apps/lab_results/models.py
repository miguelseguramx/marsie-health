from django.db import models


class Analyte(models.Model):
    class Category(models.TextChoices):
        RED_CELLS = "red_cells", "Red cells"
        RED_INDICES = "red_indices", "Red cell indices"
        WHITE_CELLS = "white_cells", "White cells"
        PLATELETS = "platelets", "Platelets"

    code = models.CharField(max_length=16, unique=True)
    name_es = models.CharField(max_length=64)
    name_en = models.CharField(max_length=64)
    default_unit = models.CharField(max_length=16)
    loinc_code = models.CharField(max_length=16, blank=True)
    category = models.CharField(max_length=16, choices=Category.choices)

    class Meta:
        ordering = ("category", "code")

    def __str__(self) -> str:
        return f"{self.code} ({self.name_en})"


class CBCResult(models.Model):
    class Flag(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    lab_report = models.ForeignKey(
        "labs.LabReport",
        on_delete=models.CASCADE,
        related_name="cbc_results",
    )
    analyte = models.ForeignKey(Analyte, on_delete=models.PROTECT)
    value = models.DecimalField(max_digits=12, decimal_places=4)
    unit = models.CharField(max_length=16)
    ref_range_low = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    ref_range_high = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    flag = models.CharField(max_length=16, choices=Flag.choices, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("lab_report", "analyte")]

    def __str__(self) -> str:
        return f"{self.analyte.code}={self.value} {self.unit}"
