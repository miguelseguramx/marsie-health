from django.urls import path

from .views import LabDashboardView, LabReportDetailView, LabReportListView

app_name = "labs"

urlpatterns = [
    path("", LabDashboardView.as_view(), name="dashboard"),
    path("results/", LabReportListView.as_view(), name="results"),
    path("results/<uuid:report_id>/", LabReportDetailView.as_view(), name="result_detail"),
]
