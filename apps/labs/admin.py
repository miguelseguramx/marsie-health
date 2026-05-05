from django.contrib import admin

from .models import Lab, LabAdminMembership, LabReport


@admin.register(Lab)
class LabAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "contact_email", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(LabAdminMembership)
class LabAdminMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "lab", "created_at")
    search_fields = ("user__email", "lab__name", "lab__slug")
    autocomplete_fields = ("user", "lab")


@admin.register(LabReport)
class LabReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "lab",
        "patient",
        "report_type",
        "status",
        "uploaded_at",
        "processed_at",
    )
    list_filter = ("status", "report_type", "lab")
    search_fields = ("content_hash", "raw_pdf_s3_key", "patient__user__email")
    readonly_fields = ("id", "uploaded_at")
    autocomplete_fields = ("lab", "patient", "uploaded_by")
