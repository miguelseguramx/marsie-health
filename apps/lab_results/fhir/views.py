"""FHIR R5 views for marsie-health.

Exposes:
  GET /fhir/DiagnosticReport          — searchset Bundle (paginated)
  GET /fhir/DiagnosticReport/{id}     — searchset Bundle for a single report
  GET /fhir/metadata                  — minimal CapabilityStatement
"""

from __future__ import annotations

from datetime import UTC, datetime

from django.db.models import OuterRef, QuerySet, Subquery
from django.shortcuts import get_object_or_404
from fhir.resources.capabilitystatement import (
    CapabilityStatement,
    CapabilityStatementRest,
    CapabilityStatementRestResource,
)
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.roles import Role, user_role
from apps.lab_results.models import CBCResult
from apps.labs.models import LabReport

from . import codings as C
from . import converters
from .exceptions import fhir_exception_handler
from .pagination import FHIRBundlePagination
from .renderers import FHIRJSONRenderer


class FHIRAPIView(APIView):
    """Base class: FHIR JSON renderer, FHIR error handler."""

    renderer_classes = [FHIRJSONRenderer]

    def get_exception_handler(self):
        return fhir_exception_handler


def _role_filtered_reports(user) -> QuerySet[LabReport]:
    role = user_role(user)
    base = LabReport.objects.select_related("lab", "patient", "patient__user")
    if role == Role.PATIENT:
        return base.filter(patient__user=user)
    if role == Role.PHYSICIAN:
        return base.filter(patient__physicians__user=user).distinct()
    if role == Role.LAB_ADMIN:
        return base.filter(lab__admins__user=user).distinct()
    return base.none()


def _apply_sort(qs: QuerySet[LabReport], sort_param: str | None) -> QuerySet[LabReport]:
    raw = sort_param or C.DEFAULT_SORT
    ordering: list[str] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        descending = token.startswith("-")
        key = token.lstrip("-")
        field = C.SORT_FIELD_MAP.get(key)
        if field is None:
            raise ValidationError(f"Unsupported _sort token: {token}")
        ordering.append(f"-{field}" if descending else field)
    if not ordering:
        ordering = ["-uploaded_at"]
    return qs.order_by(*ordering)


def _annotate_wbc(qs: QuerySet[LabReport]) -> QuerySet[LabReport]:
    wbc_subq = CBCResult.objects.filter(
        lab_report=OuterRef("pk"),
        analyte__code="WBC",
    ).values("value")[:1]
    return qs.annotate(wbc_value=Subquery(wbc_subq))


class DiagnosticReportListView(FHIRAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = FHIRBundlePagination

    def get(self, request):
        qs = _role_filtered_reports(request.user)
        qs = _apply_sort(qs, request.query_params.get("_sort"))
        qs = _annotate_wbc(qs)

        paginator = FHIRBundlePagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        # `page` is a list when pagination kicks in; if pagination is somehow
        # disabled, fall back to the full queryset.
        reports = page if page is not None else list(qs)
        total = paginator.page.paginator.count if page is not None else qs.count()
        links = paginator.get_bundle_links(request) if page is not None else []

        bundle = converters.report_search_bundle(
            reports,
            request=request,
            total=total,
            links=links or None,
        )
        return Response(bundle)


class DiagnosticReportDetailView(FHIRAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        qs = _role_filtered_reports(request.user)
        report = get_object_or_404(qs, pk=id)
        bundle = converters.report_detail_bundle(report, request=request)
        return Response(bundle)


class CapabilityStatementView(FHIRAPIView):
    """Hand-rolled minimal CapabilityStatement for /fhir/metadata."""

    authentication_classes: list = []
    permission_classes: list = []

    def get(self, request):
        statement = CapabilityStatement(
            status="active",
            date=datetime.now(tz=UTC).isoformat(),
            kind="instance",
            fhirVersion="5.0.0",
            format=["application/fhir+json"],
            rest=[
                CapabilityStatementRest(
                    mode="server",
                    resource=[
                        CapabilityStatementRestResource(
                            type="DiagnosticReport",
                            interaction=[
                                {"code": "search-type"},
                                {"code": "read"},
                            ],
                            searchInclude=[
                                "DiagnosticReport:subject",
                                "DiagnosticReport:performer",
                            ],
                        )
                    ],
                )
            ],
        )
        return Response(statement)
