from django.views.generic import TemplateView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.roles import Role


class PatientDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "patient/dashboard.html"
    required_role = Role.PATIENT
