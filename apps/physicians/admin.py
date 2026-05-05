from django.contrib import admin

from .models import CareRelationship, Physician


@admin.register(Physician)
class PhysicianAdmin(admin.ModelAdmin):
    list_display = ("user", "license_number", "specialty", "created_at")
    search_fields = ("user__email", "license_number", "specialty")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(CareRelationship)
class CareRelationshipAdmin(admin.ModelAdmin):
    list_display = (
        "physician",
        "patient",
        "consent_flag",
        "start_date",
        "end_date",
    )
    list_filter = ("consent_flag",)
    search_fields = ("physician__user__email", "patient__user__email")
    autocomplete_fields = ("physician", "patient")
