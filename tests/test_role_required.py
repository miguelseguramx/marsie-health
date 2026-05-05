import pytest
from django.test import Client


@pytest.mark.django_db
def test_unauthenticated_patient_portal_redirects_to_login():
    client = Client()
    response = client.get("/patient/")
    assert response.status_code == 302
    assert response.url.startswith("/login/")
    assert "next=/patient/" in response.url


@pytest.mark.django_db
def test_patient_cannot_access_lab_portal(patient_user):
    client = Client()
    client.force_login(patient_user)
    response = client.get("/lab/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_physician_cannot_access_patient_portal(physician_user):
    client = Client()
    client.force_login(physician_user)
    response = client.get("/patient/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_lab_admin_cannot_access_physician_portal(lab_admin_user):
    client = Client()
    client.force_login(lab_admin_user)
    response = client.get("/physician/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_patient_can_access_patient_portal(patient_user):
    client = Client()
    client.force_login(patient_user)
    response = client.get("/patient/")
    assert response.status_code == 200
