from django.views.generic import DetailView, ListView, TemplateView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.roles import Role
from apps.labs.models import LabReport


class PhysicianDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "physician/dashboard.html"
    required_role = Role.PHYSICIAN


class PhysicianReportListView(RoleRequiredMixin, ListView):
    template_name = "physician/results_list.html"
    required_role = Role.PHYSICIAN
    context_object_name = "reports"

    def get_queryset(self):
        return (
            LabReport.objects.filter(patient__physicians__user=self.request.user)
            .select_related("lab", "patient", "patient__user")
            .order_by("-uploaded_at")
            .distinct()
        )


class PhysicianReportDetailView(RoleRequiredMixin, DetailView):
    template_name = "physician/result_detail.html"
    required_role = Role.PHYSICIAN
    context_object_name = "report"
    pk_url_kwarg = "report_id"

    def get_queryset(self):
        return (
            LabReport.objects.filter(patient__physicians__user=self.request.user)
            .select_related("lab", "patient", "patient__user")
            .distinct()
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cbc_results"] = self.object.cbc_results.select_related("analyte").order_by(
            "analyte__category", "analyte__code"
        )
        return ctx
