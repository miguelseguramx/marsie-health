from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.api import LoginView, MeView, OnboardingCompleteView
from apps.labs.api import LabAdminUploadReportView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("api/auth/login/", LoginView.as_view(), name="auth-login"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("api/auth/me/", MeView.as_view(), name="auth-me"),
    path(
        "api/auth/onboarding/complete/",
        OnboardingCompleteView.as_view(),
        name="auth-onboarding-complete",
    ),
    path(
        "api/lab-admin/reports/",
        LabAdminUploadReportView.as_view(),
        name="lab-admin-upload-report",
    ),
    path("fhir/", include("apps.lab_results.fhir_urls")),
]
