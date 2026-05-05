"""Validate that every converter emits FHIR R5 resources that round-trip
through `fhir.resources` Pydantic validation, and that the list/detail
Bundles have the structure the client adapter expects.
"""

from __future__ import annotations

import json

import pytest
from django.core.management import call_command
from fhir.resources.bundle import Bundle
from fhir.resources.diagnosticreport import DiagnosticReport
from fhir.resources.observation import Observation
from fhir.resources.organization import Organization
from fhir.resources.patient import Patient
from rest_framework.test import APIClient

from apps.lab_results.fhir import codings as C
from apps.lab_results.fhir.converters import (
    cbc_result_to_observation,
    lab_to_organization,
    patient_to_fhir,
    report_to_diagnostic_report,
)
from apps.lab_results.models import CBCResult
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
    assert resp.status_code == 200, resp.data
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")


def _bundle(resp):
    """Parse a FHIR Bundle response (works regardless of renderer choice)."""
    payload = json.loads(resp.content)
    Bundle.model_validate(payload)  # raises if invalid
    return payload


@pytest.mark.django_db
class TestSingleResourceConverters:
    def test_patient_round_trip(self, seeded):
        report = LabReport.objects.filter(patient__filaxis_id="FXS-0001").first()
        fhir_patient = patient_to_fhir(report.patient)
        Patient.model_validate(fhir_patient.model_dump(exclude_none=True, by_alias=True))
        d = fhir_patient.model_dump(exclude_none=True, by_alias=True)
        assert d["resourceType"] == "Patient"
        assert d["id"] == str(report.patient.id)
        assert d["gender"] in {"male", "female", "other", "unknown"}
        assert any(i["system"] == C.PATIENT_FILAXIS_SYSTEM for i in d["identifier"])

    def test_organization_round_trip(self, seeded):
        report = LabReport.objects.first()
        org = lab_to_organization(report.lab)
        Organization.model_validate(org.model_dump(exclude_none=True, by_alias=True))
        d = org.model_dump(exclude_none=True, by_alias=True)
        assert d["resourceType"] == "Organization"
        assert d["name"] == report.lab.name
        assert any(i["system"] == C.LAB_SLUG_SYSTEM for i in d["identifier"])

    def test_diagnostic_report_round_trip_status_mapping(self, seeded):
        report = LabReport.objects.filter(status=LabReport.Status.PROCESSED).first()
        dr = report_to_diagnostic_report(report)
        DiagnosticReport.model_validate(dr.model_dump(exclude_none=True, by_alias=True))
        d = dr.model_dump(exclude_none=True, by_alias=True)
        assert d["resourceType"] == "DiagnosticReport"
        assert d["status"] == "final"  # processed -> final
        assert d["subject"]["reference"] == f"Patient/{report.patient.id}"
        assert d["performer"][0]["reference"] == f"Organization/{report.lab.id}"
        assert d["code"]["coding"][0]["code"] == C.CBC_PANEL_LOINC

    def test_observation_round_trip_with_loinc_and_ucum(self, seeded):
        cbc = CBCResult.objects.select_related("analyte").filter(analyte__code="WBC").first()
        obs = cbc_result_to_observation(cbc, patient=cbc.lab_report.patient)
        Observation.model_validate(obs.model_dump(exclude_none=True, by_alias=True))
        d = obs.model_dump(exclude_none=True, by_alias=True)
        assert d["status"] == "final"
        assert d["code"]["coding"][0]["system"] == C.LOINC_SYSTEM
        assert d["code"]["coding"][0]["code"] == "6690-2"
        assert d["valueQuantity"]["value"] == float(cbc.value)
        # Stored "10^3/uL" must be translated to UCUM "10*3/uL".
        assert d["valueQuantity"]["code"] == "10*3/uL"
        assert d["valueQuantity"]["system"] == C.UCUM_SYSTEM

    def test_observation_interpretation_codes(self, seeded):
        # Pick one CBCResult per non-empty flag value present in seed data.
        seen_flags = set()
        for cbc in CBCResult.objects.select_related("analyte").exclude(flag=""):
            if cbc.flag in seen_flags:
                continue
            seen_flags.add(cbc.flag)
            obs = cbc_result_to_observation(cbc, patient=cbc.lab_report.patient)
            d = obs.model_dump(exclude_none=True, by_alias=True)
            interp = d["interpretation"][0]["coding"][0]
            expected_code = {
                "low": "L",
                "normal": "N",
                "high": "H",
                "critical": "A",
            }[cbc.flag]
            assert interp["code"] == expected_code
            assert interp["system"] == C.INTERPRETATION_SYSTEM


@pytest.mark.django_db
class TestSearchBundle:
    def test_list_bundle_structure(self, api_client, seeded):
        _login(api_client, "labadmin@acme-lab.test", password="marsie123")
        resp = api_client.get("/fhir/DiagnosticReport")
        assert resp.status_code == 200
        assert resp["Content-Type"].startswith("application/fhir+json")
        bundle = _bundle(resp)
        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "searchset"
        assert bundle["total"] == 8
        # Match entries: every DiagnosticReport for this lab admin.
        match_drs = [
            e
            for e in bundle["entry"]
            if e["resource"]["resourceType"] == "DiagnosticReport"
            and e.get("search", {}).get("mode") == "match"
        ]
        assert len(match_drs) == 8
        # Include entries: 5 distinct patients + 1 organization for the seeded lab.
        include_patients = [
            e
            for e in bundle["entry"]
            if e["resource"]["resourceType"] == "Patient"
            and e["search"]["mode"] == "include"
        ]
        include_orgs = [
            e
            for e in bundle["entry"]
            if e["resource"]["resourceType"] == "Organization"
            and e["search"]["mode"] == "include"
        ]
        assert len(include_orgs) == 1
        assert len(include_patients) == 5

    def test_full_url_uses_absolute_fhir_base(self, api_client, seeded):
        _login(api_client, "labadmin@acme-lab.test")
        resp = api_client.get("/fhir/DiagnosticReport")
        bundle = _bundle(resp)
        for entry in bundle["entry"]:
            assert entry["fullUrl"].startswith("http")
            assert "/fhir/" in entry["fullUrl"]

    def test_wbc_summary_extension_attached(self, api_client, seeded):
        from decimal import Decimal

        _login(api_client, "labadmin@acme-lab.test")
        resp = api_client.get("/fhir/DiagnosticReport")
        bundle = _bundle(resp)
        match_drs = [
            e["resource"]
            for e in bundle["entry"]
            if e["resource"]["resourceType"] == "DiagnosticReport"
            and e["search"]["mode"] == "match"
        ]
        for dr in match_drs:
            extensions = dr.get("extension", [])
            wbc_exts = [
                ext for ext in extensions if ext["url"] == C.WBC_SUMMARY_EXTENSION
            ]
            wbc_db = CBCResult.objects.filter(
                lab_report_id=dr["id"], analyte__code="WBC"
            ).first()
            if wbc_db is None:
                assert wbc_exts == []
                continue
            assert len(wbc_exts) == 1
            sub = {x["url"]: x for x in wbc_exts[0]["extension"]}
            assert sub["value"]["valueDecimal"] == float(wbc_db.value)
            assert sub["low"]["valueBoolean"] is (wbc_db.value < Decimal("4.5"))


@pytest.mark.django_db
class TestDetailBundle:
    def test_detail_bundle_includes_observations_patient_organization(
        self, api_client, seeded
    ):
        _login(api_client, "labadmin@acme-lab.test")
        report = LabReport.objects.filter(patient__filaxis_id="FXS-0001").first()
        resp = api_client.get(f"/fhir/DiagnosticReport/{report.id}")
        assert resp.status_code == 200
        assert resp["Content-Type"].startswith("application/fhir+json")
        bundle = _bundle(resp)
        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "searchset"

        rts = [e["resource"]["resourceType"] for e in bundle["entry"]]
        assert rts.count("DiagnosticReport") == 1
        assert rts.count("Patient") == 1
        assert rts.count("Organization") == 1
        # 14 analytes per CBC panel in the seed data.
        assert rts.count("Observation") == 14

        match_dr = next(
            e["resource"]
            for e in bundle["entry"]
            if e["resource"]["resourceType"] == "DiagnosticReport"
            and e["search"]["mode"] == "match"
        )
        # DiagnosticReport.result references must resolve within the Bundle.
        ref_set = {f'{e["resource"]["resourceType"]}/{e["resource"]["id"]}' for e in bundle["entry"]}
        for ref in match_dr["result"]:
            assert ref["reference"] in ref_set


@pytest.mark.django_db
def test_capability_statement(api_client, seeded):
    resp = api_client.get("/fhir/metadata")
    assert resp.status_code == 200
    payload = json.loads(resp.content)
    assert payload["resourceType"] == "CapabilityStatement"
    assert payload["fhirVersion"] == "5.0.0"
    types = [r["type"] for r in payload["rest"][0]["resource"]]
    assert "DiagnosticReport" in types
