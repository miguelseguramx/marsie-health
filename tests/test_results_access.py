import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse

from apps.labs.models import LabReport


@pytest.fixture
def seeded(db):
    call_command("seed_dummy_data", verbosity=0)


def _user(email):
    return get_user_model().objects.get(email=email)


def _report_for(filaxis_id, index=0):
    return LabReport.objects.filter(patient__filaxis_id=filaxis_id).order_by("raw_pdf_s3_key")[
        index
    ]


@pytest.mark.django_db
class TestPatientAccess:
    def test_list_shows_only_own_reports(self, client, seeded):
        client.force_login(_user("maria.garcia@patients.test"))
        resp = client.get(reverse("patients:results"))
        assert resp.status_code == 200
        # María has 2 reports; she should not see anyone else's.
        assert len(resp.context["reports"]) == 2
        for report in resp.context["reports"]:
            assert report.patient.filaxis_id == "FXS-0001"

    def test_detail_other_patient_report_returns_404(self, client, seeded):
        client.force_login(_user("maria.garcia@patients.test"))
        ana_report = _report_for("FXS-0003")
        resp = client.get(reverse("patients:result_detail", args=[ana_report.id]))
        assert resp.status_code == 404

    def test_detail_own_report_returns_full_panel(self, client, seeded):
        client.force_login(_user("maria.garcia@patients.test"))
        own_report = _report_for("FXS-0001")
        resp = client.get(reverse("patients:result_detail", args=[own_report.id]))
        assert resp.status_code == 200
        assert len(resp.context["cbc_results"]) == 14


@pytest.mark.django_db
class TestPhysicianAccess:
    def test_list_shows_only_patients_in_care(self, client, seeded):
        client.force_login(_user("dr.gomez@doctors.test"))
        resp = client.get(reverse("physicians:results"))
        assert resp.status_code == 200
        # Dr. Gómez sees FXS-0001 (2) + FXS-0002 (2) + FXS-0003 (2) = 6 reports.
        assert len(resp.context["reports"]) == 6
        seen_ids = {r.patient.filaxis_id for r in resp.context["reports"]}
        assert seen_ids == {"FXS-0001", "FXS-0002", "FXS-0003"}

    def test_detail_out_of_care_patient_returns_404(self, client, seeded):
        client.force_login(_user("dr.gomez@doctors.test"))
        carlos_report = _report_for("FXS-0004")  # Carlos is only Dr. Fernández's patient.
        resp = client.get(reverse("physicians:result_detail", args=[carlos_report.id]))
        assert resp.status_code == 404

    def test_detail_in_care_patient_returns_200(self, client, seeded):
        client.force_login(_user("dr.gomez@doctors.test"))
        report = _report_for("FXS-0001")
        resp = client.get(reverse("physicians:result_detail", args=[report.id]))
        assert resp.status_code == 200
        assert len(resp.context["cbc_results"]) == 14

    def test_shared_patient_is_visible_to_both_physicians(self, client, seeded):
        ana_report = _report_for("FXS-0003")
        for email in ("dr.gomez@doctors.test", "dr.fernandez@doctors.test"):
            client.force_login(_user(email))
            resp = client.get(reverse("physicians:result_detail", args=[ana_report.id]))
            assert resp.status_code == 200, f"{email} should see Ana's report"


@pytest.mark.django_db
class TestLabAdminAccess:
    def test_list_sees_every_report_for_their_lab(self, client, seeded):
        client.force_login(_user("labadmin@acme-lab.test"))
        resp = client.get(reverse("labs:results"))
        assert resp.status_code == 200
        assert len(resp.context["reports"]) == 8

    def test_detail_any_report_in_their_lab_returns_200(self, client, seeded):
        client.force_login(_user("labadmin@acme-lab.test"))
        for report in LabReport.objects.all():
            resp = client.get(reverse("labs:result_detail", args=[report.id]))
            assert resp.status_code == 200, f"report {report.id} should be visible"


@pytest.mark.django_db
class TestCrossRoleGuards:
    def test_unauthenticated_redirects_to_login(self, client, seeded):
        resp = client.get(reverse("patients:results"))
        assert resp.status_code == 302
        assert "/login/" in resp.url

    def test_patient_cannot_access_lab_results(self, client, seeded):
        client.force_login(_user("maria.garcia@patients.test"))
        resp = client.get(reverse("labs:results"))
        assert resp.status_code == 403

    def test_physician_cannot_access_patient_results(self, client, seeded):
        client.force_login(_user("dr.gomez@doctors.test"))
        resp = client.get(reverse("patients:results"))
        assert resp.status_code == 403

    def test_lab_admin_cannot_access_physician_results(self, client, seeded):
        client.force_login(_user("labadmin@acme-lab.test"))
        resp = client.get(reverse("physicians:results"))
        assert resp.status_code == 403
