"""URL config for the /fhir/ namespace."""

from django.urls import path

from apps.lab_results.fhir.views import (
    CapabilityStatementView,
    DiagnosticReportDetailView,
    DiagnosticReportListView,
)

urlpatterns = [
    path("metadata", CapabilityStatementView.as_view(), name="fhir-metadata"),
    path(
        "DiagnosticReport",
        DiagnosticReportListView.as_view(),
        name="fhir-diagnosticreport-list",
    ),
    path(
        "DiagnosticReport/<uuid:id>",
        DiagnosticReportDetailView.as_view(),
        name="fhir-diagnosticreport-detail",
    ),
]
