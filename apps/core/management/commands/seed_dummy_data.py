import datetime
import hashlib
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.lab_results.models import Analyte, CBCResult
from apps.labs.models import Lab, LabReport
from apps.patients.models import Patient
from apps.physicians.models import CareRelationship, Physician

DUMMY_PASSWORD = "marsie123"  # noqa: S105 — dev-only seed
CARE_START_DATE = datetime.date(2025, 1, 1)
CARE_CONSENT_AT = datetime.datetime(2025, 1, 1, 10, 0, tzinfo=datetime.UTC)

LAB = {
    "name": "Acme Diagnostics",
    "slug": "acme-lab",
    "contact_email": "contact@acme-lab.test",
}

PATIENTS = [
    {
        "email": "maria.garcia@patients.test",
        "username": "maria.garcia",
        "first_name": "María",
        "last_name": "García",
        "filaxis_id": "FXS-0001",
        "date_of_birth": datetime.date(1985, 3, 12),
        "sex": "F",
    },
    {
        "email": "juan.lopez@patients.test",
        "username": "juan.lopez",
        "first_name": "Juan",
        "last_name": "López",
        "filaxis_id": "FXS-0002",
        "date_of_birth": datetime.date(1972, 11, 4),
        "sex": "M",
    },
    {
        "email": "ana.martinez@patients.test",
        "username": "ana.martinez",
        "first_name": "Ana",
        "last_name": "Martínez",
        "filaxis_id": "FXS-0003",
        "date_of_birth": datetime.date(1990, 7, 21),
        "sex": "F",
    },
    {
        "email": "carlos.hernandez@patients.test",
        "username": "carlos.hernandez",
        "first_name": "Carlos",
        "last_name": "Hernández",
        "filaxis_id": "FXS-0004",
        "date_of_birth": datetime.date(1968, 1, 30),
        "sex": "M",
    },
    {
        "email": "sofia.ramirez@patients.test",
        "username": "sofia.ramirez",
        "first_name": "Sofía",
        "last_name": "Ramírez",
        "filaxis_id": "FXS-0005",
        "date_of_birth": datetime.date(1995, 9, 8),
        "sex": "F",
    },
]

PHYSICIANS = [
    {
        "email": "dr.gomez@doctors.test",
        "username": "dr.gomez",
        "first_name": "Luis",
        "last_name": "Gómez",
        "license_number": "LIC-0001",
        "specialty": "Hematología",
    },
    {
        "email": "dr.fernandez@doctors.test",
        "username": "dr.fernandez",
        "first_name": "Elena",
        "last_name": "Fernández",
        "license_number": "LIC-0002",
        "specialty": "Medicina Interna",
    },
]

# (physician filaxis license, [patient filaxis IDs])
CARE_RELATIONSHIPS = [
    ("LIC-0001", ["FXS-0001", "FXS-0002", "FXS-0003"]),
    ("LIC-0002", ["FXS-0003", "FXS-0004", "FXS-0005"]),
]

# 8 reports — patient distribution by filaxis_id
REPORT_PATIENTS = [
    "FXS-0001",
    "FXS-0001",
    "FXS-0002",
    "FXS-0002",
    "FXS-0003",
    "FXS-0003",
    "FXS-0004",
    "FXS-0005",
]

# Base CBC panel from Informe Ficticio 1 (tests/test_models.py:112-127) plus reference ranges.
CBC_PANEL = [
    # (code, base_value, unit, ref_low, ref_high)
    ("HCT", 41.0, "%", 36.0, 46.0),
    ("HGB", 13.7, "g/dL", 12.0, 16.0),
    ("RBC", 4.62, "10^6/uL", 4.0, 5.5),
    ("MCV", 87.0, "fL", 80.0, 100.0),
    ("MCH", 28.4, "pg", 27.0, 33.0),
    ("MCHC", 33.2, "%", 32.0, 36.0),
    ("RDW", 12.3, "%", 11.5, 14.5),
    ("WBC", 4.95, "10^3/uL", 4.0, 11.0),
    ("NEUT_PCT", 56.0, "%", 40.0, 70.0),
    ("LYMPH_PCT", 32.0, "%", 20.0, 45.0),
    ("MONO_PCT", 6.0, "%", 2.0, 10.0),
    ("EOS_PCT", 3.0, "%", 0.0, 6.0),
    ("BASO_PCT", 1.0, "%", 0.0, 2.0),
    ("PLT", 248.0, "10^3/uL", 150.0, 450.0),
]


def vary(base: float, report_index: int, analyte_position: int) -> float:
    """Deterministic ±10 % variation so re-runs produce identical values."""
    pct = ((report_index * 7 + analyte_position) % 21 - 10) / 100.0
    return base * (1 + pct)


def compute_flag(value: float, low: float, high: float) -> str:
    if value < low:
        return CBCResult.Flag.LOW
    if value > high:
        return CBCResult.Flag.HIGH
    return CBCResult.Flag.NORMAL


def to_decimal(value: float) -> Decimal:
    return Decimal(str(round(value, 4)))


class Command(BaseCommand):
    help = "Create or refresh dummy domain data (1 lab, 5 patients, 2 physicians, 8 CBC reports)."

    @transaction.atomic
    def handle(self, *args, **opts):
        lab = self._lab()
        patients = self._patients()
        physicians = self._physicians()
        care_count = self._care_relationships(physicians, patients)
        reports = self._lab_reports(lab, patients)
        cbc_count = self._cbc_results(reports)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded: 1 lab, {len(patients)} patients, {len(physicians)} physicians, "
                f"{care_count} care relationships, {len(reports)} reports, {cbc_count} CBC results."
            )
        )

    def _lab(self) -> Lab:
        lab, created = Lab.objects.update_or_create(
            slug=LAB["slug"],
            defaults={"name": LAB["name"], "contact_email": LAB["contact_email"]},
        )
        self._log(f"Lab {lab.slug}", created)
        return lab

    def _patients(self) -> dict[str, Patient]:
        User = get_user_model()
        group = Group.objects.get(name="Patient")
        out: dict[str, Patient] = {}
        for spec in PATIENTS:
            user, user_created = User.objects.get_or_create(
                email=spec["email"],
                defaults={
                    "username": spec["username"],
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                },
            )
            if user_created:
                user.set_password(DUMMY_PASSWORD)
                user.save()
            user.groups.add(group)

            patient, p_created = Patient.objects.update_or_create(
                filaxis_id=spec["filaxis_id"],
                defaults={
                    "user": user,
                    "date_of_birth": spec["date_of_birth"],
                    "sex": spec["sex"],
                },
            )
            self._log(f"Patient {spec['filaxis_id']} ({spec['email']})", user_created or p_created)
            out[spec["filaxis_id"]] = patient
        return out

    def _physicians(self) -> dict[str, Physician]:
        User = get_user_model()
        group = Group.objects.get(name="Physician")
        out: dict[str, Physician] = {}
        for spec in PHYSICIANS:
            user, user_created = User.objects.get_or_create(
                email=spec["email"],
                defaults={
                    "username": spec["username"],
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                },
            )
            if user_created:
                user.set_password(DUMMY_PASSWORD)
                user.save()
            user.groups.add(group)

            physician, ph_created = Physician.objects.update_or_create(
                license_number=spec["license_number"],
                defaults={"user": user, "specialty": spec["specialty"]},
            )
            self._log(
                f"Physician {spec['license_number']} ({spec['email']})", user_created or ph_created
            )
            out[spec["license_number"]] = physician
        return out

    def _care_relationships(
        self,
        physicians: dict[str, Physician],
        patients: dict[str, Patient],
    ) -> int:
        count = 0
        for license_number, patient_ids in CARE_RELATIONSHIPS:
            physician = physicians[license_number]
            for filaxis_id in patient_ids:
                patient = patients[filaxis_id]
                _, created = CareRelationship.objects.get_or_create(
                    physician=physician,
                    patient=patient,
                    start_date=CARE_START_DATE,
                    defaults={
                        "consent_flag": True,
                        "consent_recorded_at": CARE_CONSENT_AT,
                    },
                )
                self._log(f"Care: {license_number} ↔ {filaxis_id}", created)
                count += 1
        return count

    def _lab_reports(
        self,
        lab: Lab,
        patients: dict[str, Patient],
    ) -> list[LabReport]:
        out: list[LabReport] = []
        for n, filaxis_id in enumerate(REPORT_PATIENTS, start=1):
            content_hash = hashlib.sha256(f"dummy-report-{n}".encode()).hexdigest()
            report, created = LabReport.objects.update_or_create(
                lab=lab,
                content_hash=content_hash,
                defaults={
                    "patient": patients[filaxis_id],
                    "report_type": LabReport.ReportType.CBC,
                    "raw_pdf_bucket": "marsie-dev",
                    "raw_pdf_s3_key": f"dummy/report-{n:02d}.pdf",
                    "status": LabReport.Status.PROCESSED,
                    "pipeline_version": "dummy-1.0",
                },
            )
            if created and report.processed_at is None:
                report.processed_at = report.uploaded_at
                report.save(update_fields=["processed_at"])
            self._log(f"LabReport #{n} for {filaxis_id}", created)
            out.append(report)
        return out

    def _cbc_results(self, reports: list[LabReport]) -> int:
        analytes = {a.code: a for a in Analyte.objects.all()}
        count = 0
        for r_index, report in enumerate(reports):
            for a_pos, (code, base, unit, low, high) in enumerate(CBC_PANEL):
                value = vary(base, r_index, a_pos)
                CBCResult.objects.update_or_create(
                    lab_report=report,
                    analyte=analytes[code],
                    defaults={
                        "value": to_decimal(value),
                        "unit": unit,
                        "ref_range_low": to_decimal(low),
                        "ref_range_high": to_decimal(high),
                        "flag": compute_flag(value, low, high),
                    },
                )
                count += 1
        return count

    def _log(self, label: str, created: bool) -> None:
        verb = "created" if created else "updated"
        self.stdout.write(f"  {verb}: {label}")
