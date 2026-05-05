from django.contrib import admin

from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("user", "filaxis_id", "date_of_birth", "sex", "created_at")
    search_fields = ("user__email", "filaxis_id")
    list_filter = ("sex",)
    readonly_fields = ("id", "created_at", "updated_at")
