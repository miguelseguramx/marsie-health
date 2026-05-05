from django.urls import path

from .views import LabDashboardView

app_name = "labs"

urlpatterns = [
    path("", LabDashboardView.as_view(), name="dashboard"),
]
