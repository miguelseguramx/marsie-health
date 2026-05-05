from django.contrib.auth.views import LoginView

from .roles import Role, user_role


class RoleBasedLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def get_success_url(self) -> str:
        next_url = self.get_redirect_url()
        if next_url:
            return next_url
        role = user_role(self.request.user)
        return {
            Role.LAB_ADMIN: "/lab/",
            Role.PHYSICIAN: "/physician/",
            Role.PATIENT: "/patient/",
        }.get(role, "/")
