from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("", include("apps.accounts.urls")),
    path("patient/", include("apps.patients.urls")),
    path("physician/", include("apps.physicians.urls")),
    path("lab/", include("apps.labs.urls")),
    path("", RedirectView.as_view(url="/login/", permanent=False)),
]
