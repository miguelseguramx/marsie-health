from django.contrib import admin

from .models import Analyte, CBCResult


@admin.register(Analyte)
class AnalyteAdmin(admin.ModelAdmin):
    list_display = ("code", "name_en", "name_es", "default_unit", "category", "loinc_code")
    list_filter = ("category",)
    search_fields = ("code", "name_en", "name_es", "loinc_code")


@admin.register(CBCResult)
class CBCResultAdmin(admin.ModelAdmin):
    list_display = (
        "analyte",
        "value",
        "unit",
        "flag",
        "lab_report",
        "created_at",
    )
    list_filter = ("flag", "analyte__category")
    search_fields = ("analyte__code", "lab_report__content_hash")
    autocomplete_fields = ("lab_report", "analyte")
