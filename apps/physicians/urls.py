from django.urls import path

from .views import PhysicianDashboardView

app_name = "physicians"

urlpatterns = [
    path("", PhysicianDashboardView.as_view(), name="dashboard"),
]
