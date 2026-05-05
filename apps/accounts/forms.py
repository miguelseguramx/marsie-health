from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User


class UserCreateForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "username")


class UserUpdateForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
