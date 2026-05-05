import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group


@pytest.fixture
def patient_user(db):
    User = get_user_model()
    user = User.objects.create_user(
        username="patient1", email="patient1@example.com", password="pw-patient-1"
    )
    user.groups.add(Group.objects.get(name="Patient"))
    return user


@pytest.fixture
def physician_user(db):
    User = get_user_model()
    user = User.objects.create_user(username="doc1", email="doc1@example.com", password="pw-doc-1")
    user.groups.add(Group.objects.get(name="Physician"))
    return user


@pytest.fixture
def lab_admin_user(db):
    User = get_user_model()
    user = User.objects.create_user(username="lab1", email="lab1@example.com", password="pw-lab-1")
    user.groups.add(Group.objects.get(name="LabAdmin"))
    return user


@pytest.fixture
def unrolled_user(db):
    User = get_user_model()
    return User.objects.create_user(
        username="nobody", email="nobody@example.com", password="pw-nobody"
    )
