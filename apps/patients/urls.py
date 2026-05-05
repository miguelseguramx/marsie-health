from django.urls import path

from .views import PatientDashboardView, PatientReportDetailView, PatientReportListView

app_name = "patients"

urlpatterns = [
    path("", PatientDashboardView.as_view(), name="dashboard"),
    path("results/", PatientReportListView.as_view(), name="results"),
    path("results/<uuid:report_id>/", PatientReportDetailView.as_view(), name="result_detail"),
]
