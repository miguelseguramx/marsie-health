from django.urls import path

from .views import PhysicianDashboardView, PhysicianReportDetailView, PhysicianReportListView

app_name = "physicians"

urlpatterns = [
    path("", PhysicianDashboardView.as_view(), name="dashboard"),
    path("results/", PhysicianReportListView.as_view(), name="results"),
    path("results/<uuid:report_id>/", PhysicianReportDetailView.as_view(), name="result_detail"),
]
