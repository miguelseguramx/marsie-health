"""ORM → FHIR R5 converters and Bundle builders for marsie-health.

Pure functions: each takes a Django model instance (already loaded with the
necessary related rows) and returns a `fhir.resources` Pydantic model.
Bundle builders compose those resources into searchset Bundles for the
list / detail endpoints exposed under /fhir/.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from typing import Any

from fhir.resources.bundle import Bundle, BundleEntry, BundleEntrySearch, BundleLink
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.diagnosticreport import DiagnosticReport
from fhir.resources.extendedcontactdetail import ExtendedContactDetail
from fhir.resources.extension import Extension
from fhir.resources.humanname import HumanName
from fhir.resources.identifier import Identifier
from fhir.resources.observation import Observation, ObservationReferenceRange
from fhir.resources.organization import Organization
from fhir.resources.patient import Patient
from fhir.resources.quantity import Quantity
from fhir.resources.reference import Reference

from apps.lab_results.models import CBCResult
from apps.labs.models import Lab, LabReport
from apps.patients.models import Patient as PatientModel

from . import codings as C

# --- helpers -----------------------------------------------------------------


def _absolute_fhir_base(request) -> str:
    """Return the absolute base URL for FHIR resources (always ends with '/')."""
    if request is None:
        return "/fhir/"
    return request.build_absolute_uri("/fhir/")


def _full_url(request, resource_type: str, resource_id: str) -> str:
    base = _absolute_fhir_base(request)
    if not base.endswith("/"):
        base = base + "/"
    return f"{base}{resource_type}/{resource_id}"


def _observation_id(report_id: str, analyte_code: str) -> str:
    # FHIR Resource.id must match `[A-Za-z0-9\-\.]{1,64}` — underscores in
    # analyte codes (e.g. NEUT_PCT) need substitution.
    safe = analyte_code.replace("_", "-")
    return f"cbc-{report_id}-{safe}"


def _patient_reference(patient: PatientModel | None) -> Reference | None:
    if patient is None:
        return None
    return Reference(reference=f"Patient/{patient.id}")


def _organization_reference(lab: Lab) -> Reference:
    return Reference(reference=f"Organization/{lab.id}")


# --- single-resource converters ---------------------------------------------


def patient_to_fhir(patient: PatientModel) -> Patient:
    user = patient.user
    identifiers: list[Identifier] = []
    if patient.filaxis_id:
        identifiers.append(
            Identifier(
                system=C.PATIENT_FILAXIS_SYSTEM,
                value=patient.filaxis_id,
                use="official",
            )
        )

    name_kwargs: dict[str, Any] = {"use": "official"}
    if user.last_name:
        name_kwargs["family"] = user.last_name
    if user.first_name:
        name_kwargs["given"] = [user.first_name]
    names = [HumanName(**name_kwargs)] if user.first_name or user.last_name else []

    telecom: list[ContactPoint] = []
    if user.email:
        telecom.append(ContactPoint(system="email", value=user.email))

    kwargs: dict[str, Any] = {
        "id": str(patient.id),
        "gender": C.gender_for(patient.sex),
    }
    if identifiers:
        kwargs["identifier"] = identifiers
    if names:
        kwargs["name"] = names
    if telecom:
        kwargs["telecom"] = telecom
    if patient.date_of_birth:
        kwargs["birthDate"] = patient.date_of_birth.isoformat()

    return Patient(**kwargs)


def lab_to_organization(lab: Lab) -> Organization:
    kwargs: dict[str, Any] = {
        "id": str(lab.id),
        "name": lab.name,
        "identifier": [Identifier(system=C.LAB_SLUG_SYSTEM, value=lab.slug)],
    }
    if lab.contact_email:
        kwargs["contact"] = [
            ExtendedContactDetail(
                telecom=[ContactPoint(system="email", value=lab.contact_email)]
            )
        ]
    return Organization(**kwargs)


def cbc_result_to_observation(cbc: CBCResult, *, patient: PatientModel | None) -> Observation:
    analyte = cbc.analyte
    report_id = str(cbc.lab_report_id)

    # code: prefer LOINC, fall back to internal analyte code system.
    if analyte.loinc_code:
        coding = Coding(
            system=C.LOINC_SYSTEM,
            code=analyte.loinc_code,
            display=analyte.name_en,
        )
    else:
        coding = Coding(
            system=C.ANALYTE_SYSTEM,
            code=analyte.code,
            display=analyte.name_en,
        )
    code = CodeableConcept(coding=[coding], text=analyte.name_en)

    quantity_kwargs: dict[str, Any] = {"value": float(cbc.value)}
    if cbc.unit:
        quantity_kwargs["unit"] = cbc.unit
        ucum = C.ucum_code_for(cbc.unit)
        if ucum:
            quantity_kwargs["system"] = C.UCUM_SYSTEM
            quantity_kwargs["code"] = ucum
    value_quantity = Quantity(**quantity_kwargs)

    ref_range: list[ObservationReferenceRange] = []
    if cbc.ref_range_low is not None or cbc.ref_range_high is not None:
        rr_kwargs: dict[str, Any] = {}
        if cbc.ref_range_low is not None:
            rr_kwargs["low"] = Quantity(
                value=float(cbc.ref_range_low),
                unit=cbc.unit or None,
                system=C.UCUM_SYSTEM if cbc.unit else None,
                code=C.ucum_code_for(cbc.unit),
            )
        if cbc.ref_range_high is not None:
            rr_kwargs["high"] = Quantity(
                value=float(cbc.ref_range_high),
                unit=cbc.unit or None,
                system=C.UCUM_SYSTEM if cbc.unit else None,
                code=C.ucum_code_for(cbc.unit),
            )
        ref_range.append(ObservationReferenceRange(**rr_kwargs))

    interpretation: list[CodeableConcept] = []
    interp = C.interpretation_for(cbc.flag)
    if interp is not None:
        interp_code, interp_display = interp
        interp_text = "critical" if cbc.flag == CBCResult.Flag.CRITICAL else interp_display
        interpretation.append(
            CodeableConcept(
                coding=[
                    Coding(
                        system=C.INTERPRETATION_SYSTEM,
                        code=interp_code,
                        display=interp_display,
                    )
                ],
                text=interp_text,
            )
        )

    obs_kwargs: dict[str, Any] = {
        "id": _observation_id(report_id, analyte.code),
        "identifier": [
            Identifier(
                system=C.OBSERVATION_SYSTEM,
                value=_observation_id(report_id, analyte.code),
            )
        ],
        "status": "final",
        "category": [
            CodeableConcept(
                coding=[
                    Coding(
                        system=C.OBSERVATION_CATEGORY_SYSTEM,
                        code="laboratory",
                        display="Laboratory",
                    )
                ]
            )
        ],
        "code": code,
        "valueQuantity": value_quantity,
    }
    subject = _patient_reference(patient)
    if subject is not None:
        obs_kwargs["subject"] = subject
    if ref_range:
        obs_kwargs["referenceRange"] = ref_range
    if interpretation:
        obs_kwargs["interpretation"] = interpretation

    return Observation(**obs_kwargs)


def report_to_diagnostic_report(
    report: LabReport,
    *,
    wbc_value: Decimal | None = None,
) -> DiagnosticReport:
    """Build a DiagnosticReport. If `wbc_value` is provided, attach the
    private wbc-summary Extension used by the list view."""
    code = CodeableConcept(
        coding=[
            Coding(
                system=C.LOINC_SYSTEM,
                code=C.CBC_PANEL_LOINC,
                display=C.CBC_PANEL_DISPLAY,
            )
        ],
        text="Complete Blood Count",
    )
    category = [
        CodeableConcept(
            coding=[
                Coding(
                    system=C.DIAGNOSTIC_SERVICE_SECTION_SYSTEM,
                    code="LAB",
                    display="Laboratory",
                )
            ]
        )
    ]

    kwargs: dict[str, Any] = {
        "id": str(report.id),
        "identifier": [
            Identifier(system=C.LAB_REPORT_SYSTEM, value=str(report.id)),
        ],
        "status": C.diagnostic_report_status(report.status),
        "category": category,
        "code": code,
        "performer": [_organization_reference(report.lab)],
    }
    subject = _patient_reference(report.patient)
    if subject is not None:
        kwargs["subject"] = subject

    effective = report.processed_at or report.uploaded_at
    if effective is not None:
        kwargs["effectiveDateTime"] = effective.isoformat()
    if report.processed_at is not None:
        kwargs["issued"] = report.processed_at.isoformat()

    cbc_results = list(getattr(report, "_prefetched_cbc_results", []))
    if not cbc_results:
        # Only build references when CBCResults are loaded; the list endpoint
        # doesn't prefetch them and just emits an empty `result`.
        cbc_results = []
    if cbc_results:
        kwargs["result"] = [
            Reference(
                reference=f"Observation/{_observation_id(str(report.id), c.analyte.code)}"
            )
            for c in cbc_results
        ]

    if wbc_value is not None:
        kwargs["extension"] = [_wbc_summary_extension(wbc_value)]

    return DiagnosticReport(**kwargs)


def _wbc_summary_extension(wbc_value: Decimal) -> Extension:
    is_low = wbc_value < C.WBC_LOW_THRESHOLD
    return Extension(
        url=C.WBC_SUMMARY_EXTENSION,
        extension=[
            Extension(url="value", valueDecimal=float(wbc_value)),
            Extension(url="low", valueBoolean=bool(is_low)),
        ],
    )


# --- Bundle builders ---------------------------------------------------------


def report_search_bundle(
    reports: Iterable[LabReport],
    *,
    request,
    total: int,
    links: list[BundleLink] | None = None,
) -> Bundle:
    """Searchset Bundle for GET /fhir/DiagnosticReport.

    Each report contributes:
      - one DiagnosticReport entry (mode=match) with a wbc-summary Extension
        when the report carries an annotated `wbc_value`,
      - one Patient entry (mode=include) per unique patient,
      - one Organization entry (mode=include) per unique lab.
    """
    entries: list[BundleEntry] = []
    seen_patients: set[str] = set()
    seen_labs: set[str] = set()

    for report in reports:
        wbc_value = getattr(report, "wbc_value", None)
        dr = report_to_diagnostic_report(report, wbc_value=wbc_value)
        entries.append(
            BundleEntry(
                fullUrl=_full_url(request, "DiagnosticReport", str(report.id)),
                resource=dr,
                search=BundleEntrySearch(mode="match"),
            )
        )
        if report.patient is not None and str(report.patient.id) not in seen_patients:
            entries.append(
                BundleEntry(
                    fullUrl=_full_url(request, "Patient", str(report.patient.id)),
                    resource=patient_to_fhir(report.patient),
                    search=BundleEntrySearch(mode="include"),
                )
            )
            seen_patients.add(str(report.patient.id))
        if str(report.lab.id) not in seen_labs:
            entries.append(
                BundleEntry(
                    fullUrl=_full_url(request, "Organization", str(report.lab.id)),
                    resource=lab_to_organization(report.lab),
                    search=BundleEntrySearch(mode="include"),
                )
            )
            seen_labs.add(str(report.lab.id))

    bundle_kwargs: dict[str, Any] = {
        "type": "searchset",
        "total": total,
        "entry": entries,
    }
    if links:
        bundle_kwargs["link"] = links
    return Bundle(**bundle_kwargs)


def report_detail_bundle(report: LabReport, *, request) -> Bundle:
    """Searchset Bundle for GET /fhir/DiagnosticReport/{id}.

    Contains the matched DiagnosticReport plus its Patient, Organization,
    and per-analyte Observations as include entries."""
    cbc_results = list(report.cbc_results.select_related("analyte").order_by(
        "analyte__category", "analyte__code"
    ))
    # Stash the prefetched list so the converter can emit DiagnosticReport.result references.
    report._prefetched_cbc_results = cbc_results  # type: ignore[attr-defined]

    entries: list[BundleEntry] = [
        BundleEntry(
            fullUrl=_full_url(request, "DiagnosticReport", str(report.id)),
            resource=report_to_diagnostic_report(report),
            search=BundleEntrySearch(mode="match"),
        )
    ]
    if report.patient is not None:
        entries.append(
            BundleEntry(
                fullUrl=_full_url(request, "Patient", str(report.patient.id)),
                resource=patient_to_fhir(report.patient),
                search=BundleEntrySearch(mode="include"),
            )
        )
    entries.append(
        BundleEntry(
            fullUrl=_full_url(request, "Organization", str(report.lab.id)),
            resource=lab_to_organization(report.lab),
            search=BundleEntrySearch(mode="include"),
        )
    )
    for cbc in cbc_results:
        obs = cbc_result_to_observation(cbc, patient=report.patient)
        entries.append(
            BundleEntry(
                fullUrl=_full_url(request, "Observation", obs.id),
                resource=obs,
                search=BundleEntrySearch(mode="include"),
            )
        )

    self_link = BundleLink(
        relation="self",
        url=_full_url(request, "DiagnosticReport", str(report.id)),
    )
    return Bundle(type="searchset", total=1, entry=entries, link=[self_link])
