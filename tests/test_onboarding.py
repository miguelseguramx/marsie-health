from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import OnboardingToken
from apps.labs.models import Lab, LabAdminMembership, LabReport
from apps.patients.models import Patient

UPLOAD_URL = "/api/lab-admin/reports/"
COMPLETE_URL = "/api/auth/onboarding/complete/"


def _pdf(content: bytes = b"%PDF-1.4 fake report bytes", name: str = "report.pdf") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, content, content_type="application/pdf")


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def lab(db):
    return Lab.objects.create(name="Test Lab", slug="test-lab")


@pytest.fixture
def lab_admin_with_lab(lab_admin_user, lab):
    LabAdminMembership.objects.create(user=lab_admin_user, lab=lab)
    return lab_admin_user


def _auth(api_client, user, password):
    resp = api_client.post(
        "/api/auth/login/",
        {"email": user.email, "password": password},
        format="json",
    )
    assert resp.status_code == 200
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")


@pytest.mark.django_db
def test_lab_admin_can_upload_for_new_patient(api_client, lab_admin_with_lab, s3_bucket):
    _auth(api_client, lab_admin_with_lab, "pw-lab-1")
    mail.outbox.clear()

    resp = api_client.post(
        UPLOAD_URL,
        {
            "patient_email": "newbie@example.com",
            "patient_first_name": "New",
            "patient_last_name": "Patient",
            "file": _pdf(b"newbie-bytes"),
        },
    )

    assert resp.status_code == 201, resp.data
    assert resp.data["email_sent"] is True
    assert resp.data["patient_email"] == "newbie@example.com"

    User = get_user_model()
    user = User.objects.get(email="newbie@example.com")
    assert not user.has_usable_password()
    assert Patient.objects.filter(user=user).exists()

    report = LabReport.objects.get(patient__user=user)
    assert report.raw_pdf_bucket == s3_bucket
    assert report.raw_pdf_s3_key.endswith(f"{report.id}.pdf")
    assert report.content_hash and not report.content_hash.startswith("pending-")

    assert OnboardingToken.objects.filter(user=user).count() == 1
    assert len(mail.outbox) == 1
    assert "newbie@example.com" in mail.outbox[0].to
    assert "/onboarding/" in mail.outbox[0].body


@pytest.mark.django_db
def test_existing_onboarded_patient_no_email(
    api_client, lab_admin_with_lab, patient_user, s3_bucket
):
    Patient.objects.create(user=patient_user)
    _auth(api_client, lab_admin_with_lab, "pw-lab-1")
    mail.outbox.clear()

    resp = api_client.post(
        UPLOAD_URL,
        {
            "patient_email": patient_user.email,
            "patient_first_name": "Already",
            "patient_last_name": "Onboarded",
            "file": _pdf(b"onboarded-bytes"),
        },
    )

    assert resp.status_code == 201
    assert resp.data["email_sent"] is False
    assert OnboardingToken.objects.filter(user=patient_user).count() == 0
    assert LabReport.objects.filter(patient__user=patient_user).count() == 1
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_second_upload_for_unonboarded_patient_issues_new_token(
    api_client, lab_admin_with_lab, s3_bucket
):
    _auth(api_client, lab_admin_with_lab, "pw-lab-1")
    base = {
        "patient_email": "again@example.com",
        "patient_first_name": "Again",
        "patient_last_name": "Patient",
    }
    api_client.post(UPLOAD_URL, {**base, "file": _pdf(b"first-report-bytes")})
    mail.outbox.clear()

    resp = api_client.post(UPLOAD_URL, {**base, "file": _pdf(b"second-report-bytes")})

    assert resp.status_code == 201
    assert resp.data["email_sent"] is True
    User = get_user_model()
    user = User.objects.get(email="again@example.com")
    assert OnboardingToken.objects.filter(user=user).count() == 2
    assert LabReport.objects.filter(patient__user=user).count() == 2
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_duplicate_upload_returns_existing_report(api_client, lab_admin_with_lab, s3_bucket):
    _auth(api_client, lab_admin_with_lab, "pw-lab-1")
    payload = {
        "patient_email": "dup@example.com",
        "patient_first_name": "Dup",
        "patient_last_name": "Patient",
    }
    body = b"%PDF-1.4 identical bytes both times"

    first = api_client.post(UPLOAD_URL, {**payload, "file": _pdf(body, name="a.pdf")})
    assert first.status_code == 201
    assert first.data["duplicate"] is False
    mail.outbox.clear()

    second = api_client.post(UPLOAD_URL, {**payload, "file": _pdf(body, name="b.pdf")})
    assert second.status_code == 200, second.data
    assert second.data["duplicate"] is True
    assert second.data["report_id"] == first.data["report_id"]
    assert second.data["email_sent"] is False

    User = get_user_model()
    user = User.objects.get(email="dup@example.com")
    assert LabReport.objects.filter(patient__user=user).count() == 1
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_non_lab_admin_cannot_upload(api_client, patient_user):
    resp = api_client.post(
        "/api/auth/login/",
        {"email": patient_user.email, "password": "pw-patient-1"},
        format="json",
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")

    resp = api_client.post(
        UPLOAD_URL,
        {
            "patient_email": "x@example.com",
            "patient_first_name": "X",
            "patient_last_name": "Y",
            "file": _pdf(),
        },
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_lab_admin_without_lab_membership_returns_400(api_client, lab_admin_user):
    _auth(api_client, lab_admin_user, "pw-lab-1")
    resp = api_client.post(
        UPLOAD_URL,
        {
            "patient_email": "x@example.com",
            "patient_first_name": "X",
            "patient_last_name": "Y",
            "file": _pdf(),
        },
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_unauthenticated_upload_returns_401(api_client):
    resp = api_client.post(
        UPLOAD_URL,
        {
            "patient_email": "x@example.com",
            "patient_first_name": "X",
            "patient_last_name": "Y",
            "file": _pdf(),
        },
    )
    assert resp.status_code == 401


@pytest.mark.django_db
def test_upload_without_file_returns_400(api_client, lab_admin_with_lab):
    _auth(api_client, lab_admin_with_lab, "pw-lab-1")
    resp = api_client.post(
        UPLOAD_URL,
        {
            "patient_email": "x@example.com",
            "patient_first_name": "X",
            "patient_last_name": "Y",
        },
    )
    assert resp.status_code == 400
    assert "file" in resp.data


@pytest.mark.django_db
def test_complete_onboarding_sets_password_and_returns_jwt(
    api_client, lab_admin_with_lab, s3_bucket
):
    _auth(api_client, lab_admin_with_lab, "pw-lab-1")
    api_client.post(
        UPLOAD_URL,
        {
            "patient_email": "set-pw@example.com",
            "patient_first_name": "Set",
            "patient_last_name": "Pw",
            "file": _pdf(b"set-pw-bytes"),
        },
    )
    token = OnboardingToken.objects.get(user__email="set-pw@example.com")
    api_client.credentials()  # drop lab admin auth

    resp = api_client.post(
        COMPLETE_URL,
        {"token": token.token, "password": "S3cur3-passw0rd!"},
        format="json",
    )

    assert resp.status_code == 200, resp.data
    assert "access" in resp.data
    assert "refresh" in resp.data
    assert resp.data["email"] == "set-pw@example.com"
    assert resp.data["role"] == "Patient"
    assert resp.data["report_id"] is not None

    User = get_user_model()
    user = User.objects.get(email="set-pw@example.com")
    assert user.has_usable_password()
    assert user.check_password("S3cur3-passw0rd!")

    token.refresh_from_db()
    assert token.consumed_at is not None


@pytest.mark.django_db
def test_complete_onboarding_replay_rejected(api_client, lab_admin_with_lab, s3_bucket):
    _auth(api_client, lab_admin_with_lab, "pw-lab-1")
    api_client.post(
        UPLOAD_URL,
        {
            "patient_email": "replay@example.com",
            "patient_first_name": "R",
            "patient_last_name": "P",
            "file": _pdf(b"replay-bytes"),
        },
    )
    token = OnboardingToken.objects.get(user__email="replay@example.com")
    api_client.credentials()

    first = api_client.post(
        COMPLETE_URL,
        {"token": token.token, "password": "S3cur3-passw0rd!"},
        format="json",
    )
    assert first.status_code == 200

    second = api_client.post(
        COMPLETE_URL,
        {"token": token.token, "password": "S3cur3-passw0rd!"},
        format="json",
    )
    assert second.status_code == 400
    assert "already" in second.data["detail"].lower()


@pytest.mark.django_db
def test_complete_onboarding_expired_token_rejected(
    api_client, lab_admin_with_lab, s3_bucket
):
    _auth(api_client, lab_admin_with_lab, "pw-lab-1")
    api_client.post(
        UPLOAD_URL,
        {
            "patient_email": "expired@example.com",
            "patient_first_name": "E",
            "patient_last_name": "P",
            "file": _pdf(b"expired-bytes"),
        },
    )
    token = OnboardingToken.objects.get(user__email="expired@example.com")
    token.expires_at = timezone.now() - timedelta(seconds=1)
    token.save(update_fields=["expires_at"])
    api_client.credentials()

    resp = api_client.post(
        COMPLETE_URL,
        {"token": token.token, "password": "S3cur3-passw0rd!"},
        format="json",
    )
    assert resp.status_code == 400
    assert "expired" in resp.data["detail"].lower()


@pytest.mark.django_db
def test_complete_onboarding_unknown_token_rejected(api_client):
    resp = api_client.post(
        COMPLETE_URL,
        {"token": "does-not-exist", "password": "S3cur3-passw0rd!"},
        format="json",
    )
    assert resp.status_code == 400
    assert "invalid" in resp.data["detail"].lower() or "unknown" in resp.data["detail"].lower()
