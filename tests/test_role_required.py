import json

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


def _login(api_client, email, password):
    resp = api_client.post(
        "/api/auth/login/",
        {"email": email, "password": password},
        format="json",
    )
    assert resp.status_code == 200
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")


@pytest.mark.django_db
def test_unauthenticated_reports_returns_401(api_client):
    response = api_client.get("/fhir/DiagnosticReport")
    assert response.status_code == 401
    payload = json.loads(response.content)
    assert payload["resourceType"] == "OperationOutcome"
    assert payload["issue"][0]["code"] == "security"


@pytest.mark.django_db
def test_unauthenticated_me_returns_401(api_client):
    response = api_client.get("/api/auth/me/")
    assert response.status_code == 401


@pytest.mark.django_db
def test_patient_reports_returns_200(api_client, patient_user):
    _login(api_client, patient_user.email, "pw-patient-1")
    response = api_client.get("/fhir/DiagnosticReport")
    assert response.status_code == 200


@pytest.mark.django_db
def test_unrolled_user_reports_returns_empty_200(api_client, unrolled_user):
    _login(api_client, unrolled_user.email, "pw-nobody")
    response = api_client.get("/fhir/DiagnosticReport")
    assert response.status_code == 200
    bundle = json.loads(response.content)
    assert bundle["resourceType"] == "Bundle"
    assert bundle["total"] == 0
    matches = [
        e for e in bundle.get("entry", [])
        if e["resource"]["resourceType"] == "DiagnosticReport"
        and e["search"]["mode"] == "match"
    ]
    assert matches == []
