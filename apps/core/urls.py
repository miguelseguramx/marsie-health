from django.urls import path

from .views import HealthzView

urlpatterns = [
    path("healthz/", HealthzView.as_view(), name="healthz"),
]
