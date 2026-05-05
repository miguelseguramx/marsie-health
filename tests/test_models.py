import datetime
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from apps.lab_results.models import Analyte, CBCResult
from apps.labs.models import Lab, LabReport
from apps.patients.models import Patient
from apps.physicians.models import CareRelationship, Physician


@pytest.fixture
def User():
    return get_user_model()


@pytest.fixture
def lab(db):
    return Lab.objects.create(name="Lab One", slug="lab-one", contact_email="a@b.com")


@pytest.fixture
def patient(db, User):
    user = User.objects.create_user(username="p", email="p@x.com", password="x")
    return Patient.objects.create(user=user, filaxis_id="FXS-001")


@pytest.fixture
def physician(db, User):
    user = User.objects.create_user(username="d", email="d@x.com", password="x")
    return Physician.objects.create(user=user, license_number="LIC-001")


@pytest.mark.django_db
def test_patient_user_is_unique(User, patient):
    user = patient.user
    with pytest.raises(IntegrityError), transaction.atomic():
        Patient.objects.create(user=user)


@pytest.mark.django_db
def test_lab_report_dedup_on_lab_and_content_hash(lab, patient, User):
    LabReport.objects.create(
        lab=lab,
        patient=patient,
        raw_pdf_bucket="b",
        raw_pdf_s3_key="k1",
        content_hash="h1",
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        LabReport.objects.create(
            lab=lab,
            patient=patient,
            raw_pdf_bucket="b",
            raw_pdf_s3_key="k2",
            content_hash="h1",
        )


@pytest.mark.django_db
def test_lab_report_same_hash_different_lab_is_allowed(lab, patient):
    other_lab = Lab.objects.create(name="Lab Two", slug="lab-two")
    LabReport.objects.create(lab=lab, raw_pdf_bucket="b", raw_pdf_s3_key="k", content_hash="hh")
    LabReport.objects.create(
        lab=other_lab, raw_pdf_bucket="b", raw_pdf_s3_key="k", content_hash="hh"
    )
    assert LabReport.objects.count() == 2


@pytest.mark.django_db
def test_care_relationship_unique_on_physician_patient_start_date(physician, patient):
    today = datetime.date.today()
    CareRelationship.objects.create(physician=physician, patient=patient, start_date=today)
    with pytest.raises(IntegrityError), transaction.atomic():
        CareRelationship.objects.create(physician=physician, patient=patient, start_date=today)


@pytest.mark.django_db
def test_care_relationship_allows_new_consent_epoch(physician, patient):
    CareRelationship.objects.create(
        physician=physician, patient=patient, start_date=datetime.date(2024, 1, 1)
    )
    CareRelationship.objects.create(
        physician=physician, patient=patient, start_date=datetime.date(2025, 1, 1)
    )
    assert CareRelationship.objects.filter(physician=physician).count() == 2


@pytest.mark.django_db
def test_cbc_result_unique_on_lab_report_and_analyte(lab):
    report = LabReport.objects.create(
        lab=lab, raw_pdf_bucket="b", raw_pdf_s3_key="k", content_hash="rep1"
    )
    hgb = Analyte.objects.get(code="HGB")
    CBCResult.objects.create(lab_report=report, analyte=hgb, value=13.7, unit="g/dL")
    with pytest.raises(IntegrityError), transaction.atomic():
        CBCResult.objects.create(lab_report=report, analyte=hgb, value=14.0, unit="g/dL")


@pytest.mark.django_db
def test_full_cbc_panel_inserts(lab, patient):
    """Insert all 14 sample CBC analytes into one report — mirrors Informe Ficticio 1."""
    report = LabReport.objects.create(
        lab=lab,
        patient=patient,
        raw_pdf_bucket="b",
        raw_pdf_s3_key="ficticio-1.pdf",
        content_hash=uuid.uuid4().hex,
    )
    sample = {
        "HCT": ("41", "%"),
        "HGB": ("13.7", "g/dL"),
        "RBC": ("4.62", "10^6/uL"),
        "MCV": ("87", "fL"),
        "MCH": ("28.4", "pg"),
        "MCHC": ("33.2", "%"),
        "RDW": ("12.3", "%"),
        "WBC": ("4.95", "10^3/uL"),
        "NEUT_PCT": ("56", "%"),
        "LYMPH_PCT": ("32", "%"),
        "MONO_PCT": ("6", "%"),
        "EOS_PCT": ("3", "%"),
        "BASO_PCT": ("1", "%"),
        "PLT": ("248", "10^3/uL"),
    }
    for code, (value, unit) in sample.items():
        CBCResult.objects.create(
            lab_report=report,
            analyte=Analyte.objects.get(code=code),
            value=value,
            unit=unit,
        )
    assert report.cbc_results.count() == 14
