"""Bundle pagination + _sort param semantics for /fhir/DiagnosticReport."""

from __future__ import annotations

import json

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient


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


def _bundle(resp):
    return json.loads(resp.content)


def _link_rels(bundle):
    return {link["relation"] for link in bundle.get("link", [])}


def _link_url(bundle, relation):
    for link in bundle.get("link", []):
        if link["relation"] == relation:
            return link["url"]
    return None


@pytest.mark.django_db
def test_default_page_emits_self_first_last(api_client, seeded):
    _login(api_client, "labadmin@acme-lab.test")
    resp = api_client.get("/fhir/DiagnosticReport")
    assert resp.status_code == 200
    bundle = _bundle(resp)
    rels = _link_rels(bundle)
    assert {"self", "first", "last"} <= rels
    # 8 reports, default _count=20 -> all on page 1, no next/previous.
    assert "next" not in rels
    assert "previous" not in rels


@pytest.mark.django_db
def test_count_param_paginates_and_emits_next(api_client, seeded):
    _login(api_client, "labadmin@acme-lab.test")
    resp = api_client.get("/fhir/DiagnosticReport?_count=3")
    bundle = _bundle(resp)
    rels = _link_rels(bundle)
    assert {"self", "first", "next", "last"} <= rels
    next_url = _link_url(bundle, "next")
    assert "page=2" in next_url
    assert "_count=3" in next_url
    # 3 match entries on page 1.
    matches = [
        e for e in bundle["entry"]
        if e["resource"]["resourceType"] == "DiagnosticReport"
        and e["search"]["mode"] == "match"
    ]
    assert len(matches) == 3
    assert bundle["total"] == 8


@pytest.mark.django_db
def test_following_next_link_returns_page_2(api_client, seeded):
    _login(api_client, "labadmin@acme-lab.test")
    resp = api_client.get("/fhir/DiagnosticReport?_count=5")
    bundle = _bundle(resp)
    next_url = _link_url(bundle, "next")
    # Strip host so APIClient hits the relative path.
    from urllib.parse import urlparse
    parsed = urlparse(next_url)
    rel_path = parsed.path + ("?" + parsed.query if parsed.query else "")
    resp2 = api_client.get(rel_path)
    assert resp2.status_code == 200
    bundle2 = _bundle(resp2)
    matches = [
        e for e in bundle2["entry"]
        if e["resource"]["resourceType"] == "DiagnosticReport"
        and e["search"]["mode"] == "match"
    ]
    # Page 2 of 8 with size 5 -> 3 entries.
    assert len(matches) == 3
    rels = _link_rels(bundle2)
    assert "previous" in rels
    assert "next" not in rels


@pytest.mark.django_db
def test_sort_by_status_descending(api_client, seeded):
    _login(api_client, "labadmin@acme-lab.test")
    resp = api_client.get("/fhir/DiagnosticReport?_sort=-status")
    assert resp.status_code == 200
    bundle = _bundle(resp)
    statuses = [
        e["resource"]["status"]
        for e in bundle["entry"]
        if e["resource"]["resourceType"] == "DiagnosticReport"
        and e["search"]["mode"] == "match"
    ]
    assert statuses == sorted(statuses, reverse=True)


@pytest.mark.django_db
def test_invalid_sort_returns_operation_outcome(api_client, seeded):
    _login(api_client, "labadmin@acme-lab.test")
    resp = api_client.get("/fhir/DiagnosticReport?_sort=bogus")
    assert resp.status_code == 400
    payload = json.loads(resp.content)
    assert payload["resourceType"] == "OperationOutcome"
    assert payload["issue"][0]["severity"] == "error"
    assert payload["issue"][0]["code"] == "invalid"
