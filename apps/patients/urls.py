from django.urls import path

from .views import PatientDashboardView

app_name = "patients"

urlpatterns = [
    path("", PatientDashboardView.as_view(), name="dashboard"),
]
