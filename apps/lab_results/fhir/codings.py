"""FHIR R5 coding constants and translation tables for marsie-health."""

from decimal import Decimal

from apps.lab_results.models import CBCResult
from apps.labs.models import LabReport

# --- Code system URIs ---------------------------------------------------------

LOINC_SYSTEM = "http://loinc.org"
UCUM_SYSTEM = "http://unitsofmeasure.org"
OBSERVATION_CATEGORY_SYSTEM = "http://terminology.hl7.org/CodeSystem/observation-category"
DIAGNOSTIC_SERVICE_SECTION_SYSTEM = "http://terminology.hl7.org/CodeSystem/v2-0074"
INTERPRETATION_SYSTEM = "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation"

# Marsie-internal identifier and extension namespaces.
MARSIE_BASE = "https://marsie.health"
PATIENT_FILAXIS_SYSTEM = f"{MARSIE_BASE}/filaxis"
LAB_SLUG_SYSTEM = f"{MARSIE_BASE}/lab-slug"
LAB_REPORT_SYSTEM = f"{MARSIE_BASE}/lab-report"
OBSERVATION_SYSTEM = f"{MARSIE_BASE}/observation"
ANALYTE_SYSTEM = f"{MARSIE_BASE}/analyte"
WBC_SUMMARY_EXTENSION = f"{MARSIE_BASE}/StructureDefinition/wbc-summary"

# CBC panel LOINC code (Complete Blood Count panel - automated).
CBC_PANEL_LOINC = "58410-2"
CBC_PANEL_DISPLAY = "CBC panel - Blood by Automated count"

# WBC low threshold matches the legacy serializer (4.5 x10^3/uL).
WBC_LOW_THRESHOLD = Decimal("4.5")

# --- Sex / gender mapping -----------------------------------------------------

SEX_TO_GENDER = {"M": "male", "F": "female", "O": "other"}


def gender_for(sex: str | None) -> str:
    """Map our Patient.sex -> FHIR Patient.gender. Empty/unknown -> 'unknown'."""
    if not sex:
        return "unknown"
    return SEX_TO_GENDER.get(sex, "unknown")


# --- DiagnosticReport.status mapping -----------------------------------------

# LabReport.Status -> DiagnosticReport.status (FHIR R5).
LAB_REPORT_STATUS_TO_FHIR = {
    LabReport.Status.RECEIVED: "registered",
    LabReport.Status.PROCESSING: "partial",
    LabReport.Status.PROCESSED: "final",
    LabReport.Status.FAILED: "cancelled",
}

# Inverse map for the client adapter (and sort-param translation).
FHIR_STATUS_TO_LAB_REPORT = {v: k.value for k, v in LAB_REPORT_STATUS_TO_FHIR.items()}


def diagnostic_report_status(lab_report_status: str) -> str:
    return LAB_REPORT_STATUS_TO_FHIR.get(lab_report_status, "registered")


# --- Observation.interpretation mapping --------------------------------------

# CBCResult.flag -> v3-ObservationInterpretation code.
# `critical` lacks a single canonical HL7 code; emit `A` (Abnormal) and let the
# `text` carry the original "critical" semantics. Documented as lossy.
INTERPRETATION_BY_FLAG = {
    CBCResult.Flag.LOW: ("L", "Low"),
    CBCResult.Flag.NORMAL: ("N", "Normal"),
    CBCResult.Flag.HIGH: ("H", "High"),
    CBCResult.Flag.CRITICAL: ("A", "Abnormal"),
}


def interpretation_for(flag: str) -> tuple[str, str] | None:
    if not flag:
        return None
    return INTERPRETATION_BY_FLAG.get(flag)


# --- UCUM unit translation ---------------------------------------------------

# Stored units in our seed data are not literal UCUM (we use 10^3/uL; UCUM is
# 10*3/uL). Translate before populating Quantity.code.
UCUM_BY_UNIT = {
    "%": "%",
    "g/dL": "g/dL",
    "fL": "fL",
    "pg": "pg",
    "10^3/uL": "10*3/uL",
    "10^6/uL": "10*6/uL",
}


def ucum_code_for(unit: str | None) -> str | None:
    if not unit:
        return None
    return UCUM_BY_UNIT.get(unit, unit)


# --- _sort param mapping -----------------------------------------------------

# FHIR _sort token -> Django ORM order_by field. `-` prefix is preserved.
SORT_FIELD_MAP = {
    "_lastUpdated": "uploaded_at",
    "status": "status",
    "subject": "patient__filaxis_id",
}

DEFAULT_SORT = "-_lastUpdated"
