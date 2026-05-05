from django.views.generic import DetailView, ListView, TemplateView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.roles import Role
from apps.labs.models import LabReport


class PatientDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "patient/dashboard.html"
    required_role = Role.PATIENT


class PatientReportListView(RoleRequiredMixin, ListView):
    template_name = "patient/results_list.html"
    required_role = Role.PATIENT
    context_object_name = "reports"

    def get_queryset(self):
        return (
            LabReport.objects.filter(patient__user=self.request.user)
            .select_related("lab", "patient")
            .order_by("-uploaded_at")
        )


class PatientReportDetailView(RoleRequiredMixin, DetailView):
    template_name = "patient/result_detail.html"
    required_role = Role.PATIENT
    context_object_name = "report"
    pk_url_kwarg = "report_id"

    def get_queryset(self):
        return LabReport.objects.filter(patient__user=self.request.user).select_related(
            "lab", "patient"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cbc_results"] = self.object.cbc_results.select_related("analyte").order_by(
            "analyte__category", "analyte__code"
        )
        return ctx
