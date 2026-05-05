from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .forms import UserCreateForm, UserUpdateForm
from .models import Profile, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = UserCreateForm
    form = UserUpdateForm
    model = User

    ordering = ("email",)
    list_display = ("email", "username", "is_staff", "roles_display")
    list_filter = ("is_staff", "is_superuser", "groups")
    search_fields = ("email", "username", "first_name", "last_name")

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "password1", "password2"),
            },
        ),
    )

    @admin.display(description="Roles")
    def roles_display(self, obj):
        return ", ".join(g.name for g in obj.groups.all())


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "locale", "timezone", "accepted_tos_at")
    search_fields = ("user__email", "phone")
