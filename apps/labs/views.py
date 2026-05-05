from django.views.generic import TemplateView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.roles import Role


class LabDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "lab/dashboard.html"
    required_role = Role.LAB_ADMIN
