from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(LoginRequiredMixin):
    """Allow only authenticated users in the named Django Group.

    Set `required_role` on the subclass (matches a Group name).
    Unauthenticated users are redirected to LOGIN_URL by LoginRequiredMixin;
    authenticated users without the role get a 403.
    """

    required_role: str | None = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if self.required_role and not request.user.groups.filter(name=self.required_role).exists():
            raise PermissionDenied("Your account is not assigned to this portal.")
        return super().dispatch(request, *args, **kwargs)
