from django.contrib.auth.models import Group


class Role:
    PATIENT = "Patient"
    PHYSICIAN = "Physician"
    LAB_ADMIN = "LabAdmin"

    ALL = (LAB_ADMIN, PHYSICIAN, PATIENT)


# Highest-precedence first — used by user_role() when a user is in multiple groups.
_PRECEDENCE = (Role.LAB_ADMIN, Role.PHYSICIAN, Role.PATIENT)


def assign_role(user, role: str) -> None:
    group, _ = Group.objects.get_or_create(name=role)
    user.groups.add(group)


def user_role(user) -> str | None:
    if not user.is_authenticated:
        return None
    names = set(user.groups.values_list("name", flat=True))
    for role in _PRECEDENCE:
        if role in names:
            return role
    return None
