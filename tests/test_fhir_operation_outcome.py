"""Errors on /fhir/* endpoints must surface as FHIR OperationOutcome."""

from __future__ import annotations

import json
import uuid

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.labs.models import LabReport


@pytest.fixture
def seeded(db):
    call_command("seed_dummy_data", verbosity=0)


@pytest.fixture
def api_client():
    return APIClient()


def _login(api_client, email, password="marsie123"):
    resp = api_client.post(
        "/api/auth/login/",
        {"email": email, "password": password},
        format="json",
    )
    assert resp.status_code == 200
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")


def _outcome(resp):
    payload = json.loads(resp.content)
    assert payload["resourceType"] == "OperationOutcome"
    assert payload["issue"][0]["severity"] == "error"
    return payload


@pytest.mark.django_db
def test_unauthenticated_list_returns_operation_outcome_security(api_client):
    resp = api_client.get("/fhir/DiagnosticReport")
    assert resp.status_code == 401
    outcome = _outcome(resp)
    assert outcome["issue"][0]["code"] == "security"


@pytest.mark.django_db
def test_cross_role_detail_returns_not_found(api_client, seeded):
    # Maria (FXS-0001) tries to read Ana's report (FXS-0003).
    _login(api_client, "maria.garcia@patients.test")
    ana_report = LabReport.objects.filter(patient__filaxis_id="FXS-0003").first()
    resp = api_client.get(f"/fhir/DiagnosticReport/{ana_report.id}")
    assert resp.status_code == 404
    outcome = _outcome(resp)
    assert outcome["issue"][0]["code"] == "not-found"


@pytest.mark.django_db
def test_unknown_id_returns_not_found(api_client, seeded):
    _login(api_client, "labadmin@acme-lab.test")
    resp = api_client.get(f"/fhir/DiagnosticReport/{uuid.uuid4()}")
    assert resp.status_code == 404
    outcome = _outcome(resp)
    assert outcome["issue"][0]["code"] == "not-found"


@pytest.mark.django_db
def test_invalid_sort_param_returns_invalid(api_client, seeded):
    _login(api_client, "labadmin@acme-lab.test")
    resp = api_client.get("/fhir/DiagnosticReport?_sort=foo")
    assert resp.status_code == 400
    outcome = _outcome(resp)
    assert outcome["issue"][0]["code"] == "invalid"
