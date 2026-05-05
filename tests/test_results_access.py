import json
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.lab_results.fhir.codings import (
    PATIENT_FILAXIS_SYSTEM,
    WBC_SUMMARY_EXTENSION,
)
from apps.labs.models import LabReport


@pytest.fixture
def seeded(db):
    call_command("seed_dummy_data", verbosity=0)


@pytest.fixture
def api_client():
    return APIClient()


def _user(email):
    return get_user_model().objects.get(email=email)


def _report_for(filaxis_id, index=0):
    return LabReport.objects.filter(patient__filaxis_id=filaxis_id).order_by("raw_pdf_s3_key")[
        index
    ]


def _login(api_client, email):
    resp = api_client.post(
        "/api/auth/login/",
        {"email": email, "password": "marsie123"},
        format="json",
    )
    assert resp.status_code == 200, f"login for {email} returned {resp.status_code}: {resp.data!r}"
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")


def _bundle(resp):
    return json.loads(resp.content)


def _match_reports(bundle):
    return [
        e["resource"]
        for e in bundle.get("entry", [])
        if e["resource"]["resourceType"] == "DiagnosticReport"
        and e.get("search", {}).get("mode") == "match"
    ]


def _filaxis_for(bundle, dr):
    """Resolve the patient_filaxis_id of a DiagnosticReport by walking the
    Bundle's include entries and reading Patient.identifier."""
    target_ref = dr["subject"]["reference"]
    for entry in bundle["entry"]:
        res = entry["resource"]
        if res["resourceType"] != "Patient":
            continue
        if f"Patient/{res['id']}" != target_ref:
            continue
        for ident in res.get("identifier", []):
            if ident.get("system") == PATIENT_FILAXIS_SYSTEM:
                return ident["value"]
    return None


@pytest.mark.django_db
class TestPatientAccess:
    def test_list_shows_only_own_reports(self, api_client, seeded):
        _login(api_client, "maria.garcia@patients.test")
        resp = api_client.get("/fhir/DiagnosticReport")
        assert resp.status_code == 200
        bundle = _bundle(resp)
        assert bundle["total"] == 2
        matches = _match_reports(bundle)
        assert len(matches) == 2
        for dr in matches:
            assert _filaxis_for(bundle, dr) == "FXS-0001"

    def test_detail_other_patient_report_returns_404(self, api_client, seeded):
        _login(api_client, "maria.garcia@patients.test")
        ana_report = _report_for("FXS-0003")
        resp = api_client.get(f"/fhir/DiagnosticReport/{ana_report.id}")
        assert resp.status_code == 404

    def test_detail_own_report_returns_full_panel(self, api_client, seeded):
        _login(api_client, "maria.garcia@patients.test")
        own_report = _report_for("FXS-0001")
        resp = api_client.get(f"/fhir/DiagnosticReport/{own_report.id}")
        assert resp.status_code == 200
        bundle = _bundle(resp)
        observations = [
            e for e in bundle["entry"] if e["resource"]["resourceType"] == "Observation"
        ]
        assert len(observations) == 14


@pytest.mark.django_db
class TestPhysicianAccess:
    def test_list_shows_only_patients_in_care(self, api_client, seeded):
        _login(api_client, "dr.gomez@doctors.test")
        resp = api_client.get("/fhir/DiagnosticReport")
        assert resp.status_code == 200
        bundle = _bundle(resp)
        # Dr. Gómez sees FXS-0001 (2) + FXS-0002 (2) + FXS-0003 (2) = 6 reports.
        assert bundle["total"] == 6
        matches = _match_reports(bundle)
        assert len(matches) == 6
        seen_ids = {_filaxis_for(bundle, dr) for dr in matches}
        assert seen_ids == {"FXS-0001", "FXS-0002", "FXS-0003"}

    def test_detail_out_of_care_patient_returns_404(self, api_client, seeded):
        _login(api_client, "dr.gomez@doctors.test")
        carlos_report = _report_for("FXS-0004")  # Carlos is only Dr. Fernández's patient.
        resp = api_client.get(f"/fhir/DiagnosticReport/{carlos_report.id}")
        assert resp.status_code == 404

    def test_detail_in_care_patient_returns_200(self, api_client, seeded):
        _login(api_client, "dr.gomez@doctors.test")
        report = _report_for("FXS-0001")
        resp = api_client.get(f"/fhir/DiagnosticReport/{report.id}")
        assert resp.status_code == 200
        bundle = _bundle(resp)
        observations = [
            e for e in bundle["entry"] if e["resource"]["resourceType"] == "Observation"
        ]
        assert len(observations) == 14

    def test_shared_patient_is_visible_to_both_physicians(self, api_client, seeded):
        ana_report = _report_for("FXS-0003")
        for email in ("dr.gomez@doctors.test", "dr.fernandez@doctors.test"):
            client = APIClient()
            _login(client, email)
            resp = client.get(f"/fhir/DiagnosticReport/{ana_report.id}")
            assert resp.status_code == 200, f"{email} should see Ana's report"

    def test_list_includes_wbc_summary_extension(self, api_client, seeded):
        from apps.lab_results.models import CBCResult

        _login(api_client, "dr.gomez@doctors.test")
        resp = api_client.get("/fhir/DiagnosticReport")
        assert resp.status_code == 200
        bundle = _bundle(resp)
        for dr in _match_reports(bundle):
            wbc_exts = [
                ext for ext in dr.get("extension", []) if ext["url"] == WBC_SUMMARY_EXTENSION
            ]
            assert len(wbc_exts) == 1
            sub = {x["url"]: x for x in wbc_exts[0]["extension"]}
            wbc_db = CBCResult.objects.get(lab_report_id=dr["id"], analyte__code="WBC")
            assert sub["value"]["valueDecimal"] == float(wbc_db.value)
            assert sub["low"]["valueBoolean"] is (wbc_db.value < Decimal("4.5"))


@pytest.mark.django_db
class TestLabAdminAccess:
    def test_list_sees_every_report_for_their_lab(self, api_client, seeded):
        _login(api_client, "labadmin@acme-lab.test")
        resp = api_client.get("/fhir/DiagnosticReport")
        assert resp.status_code == 200
        bundle = _bundle(resp)
        assert bundle["total"] == 8
        matches = _match_reports(bundle)
        assert len(matches) == 8

    def test_detail_any_report_in_their_lab_returns_200(self, api_client, seeded):
        _login(api_client, "labadmin@acme-lab.test")
        for report in LabReport.objects.all():
            resp = api_client.get(f"/fhir/DiagnosticReport/{report.id}")
            assert resp.status_code == 200, f"report {report.id} should be visible"


@pytest.mark.django_db
class TestCrossRoleGuards:
    def test_unauthenticated_request_returns_401(self, api_client, seeded):
        resp = api_client.get("/fhir/DiagnosticReport")
        assert resp.status_code == 401
        outcome = _bundle(resp)
        assert outcome["resourceType"] == "OperationOutcome"

    def test_patient_list_returns_only_patient_reports(self, api_client, seeded):
        _login(api_client, "maria.garcia@patients.test")
        resp = api_client.get("/fhir/DiagnosticReport")
        assert resp.status_code == 200
        bundle = _bundle(resp)
        assert bundle["total"] == 2
        assert len(_match_reports(bundle)) == 2

    def test_physician_list_returns_only_physician_reports(self, api_client, seeded):
        _login(api_client, "dr.gomez@doctors.test")
        resp = api_client.get("/fhir/DiagnosticReport")
        assert resp.status_code == 200
        bundle = _bundle(resp)
        assert bundle["total"] == 6
        assert len(_match_reports(bundle)) == 6

    def test_unrolled_user_sees_empty_list(self, api_client, seeded, unrolled_user):
        # The unrolled_user fixture creates a user with password pw-nobody (no Group membership).
        resp = api_client.post(
            "/api/auth/login/",
            {"email": unrolled_user.email, "password": "pw-nobody"},
            format="json",
        )
        assert resp.status_code == 200
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
        resp = api_client.get("/fhir/DiagnosticReport")
        assert resp.status_code == 200
        bundle = _bundle(resp)
        assert bundle["total"] == 0
        assert _match_reports(bundle) == []
