from django.views.generic import TemplateView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.roles import Role


class PhysicianDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "physician/dashboard.html"
    required_role = Role.PHYSICIAN
