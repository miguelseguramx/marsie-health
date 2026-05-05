import pytest
from django.test import Client


@pytest.mark.django_db
def test_patient_login_lands_on_patient_portal(patient_user):
    client = Client()
    response = client.post(
        "/login/",
        {"username": patient_user.email, "password": "pw-patient-1"},
    )
    assert response.status_code == 302
    assert response.url == "/patient/"


@pytest.mark.django_db
def test_physician_login_lands_on_physician_portal(physician_user):
    client = Client()
    response = client.post(
        "/login/",
        {"username": physician_user.email, "password": "pw-doc-1"},
    )
    assert response.status_code == 302
    assert response.url == "/physician/"


@pytest.mark.django_db
def test_lab_admin_login_lands_on_lab_portal(lab_admin_user):
    client = Client()
    response = client.post(
        "/login/",
        {"username": lab_admin_user.email, "password": "pw-lab-1"},
    )
    assert response.status_code == 302
    assert response.url == "/lab/"


@pytest.mark.django_db
def test_unrolled_user_lands_on_root(unrolled_user):
    client = Client()
    response = client.post(
        "/login/",
        {"username": unrolled_user.email, "password": "pw-nobody"},
    )
    assert response.status_code == 302
    assert response.url == "/"


@pytest.mark.django_db
def test_login_respects_next_parameter(patient_user):
    client = Client()
    response = client.post(
        "/login/?next=/patient/some-path/",
        {"username": patient_user.email, "password": "pw-patient-1"},
    )
    assert response.status_code == 302
    assert response.url == "/patient/some-path/"
