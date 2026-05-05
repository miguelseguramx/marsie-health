import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_patient_login_returns_jwt_with_role(api_client, patient_user):
    response = api_client.post(
        "/api/auth/login/",
        {"email": patient_user.email, "password": "pw-patient-1"},
        format="json",
    )
    assert response.status_code == 200
    assert set(response.data.keys()) >= {"access", "refresh", "email", "role"}
    assert response.data["email"] == patient_user.email
    assert response.data["role"] == "Patient"


@pytest.mark.django_db
def test_physician_login_returns_jwt_with_role(api_client, physician_user):
    response = api_client.post(
        "/api/auth/login/",
        {"email": physician_user.email, "password": "pw-doc-1"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["email"] == physician_user.email
    assert response.data["role"] == "Physician"


@pytest.mark.django_db
def test_lab_admin_login_returns_jwt_with_role(api_client, lab_admin_user):
    response = api_client.post(
        "/api/auth/login/",
        {"email": lab_admin_user.email, "password": "pw-lab-1"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["email"] == lab_admin_user.email
    assert response.data["role"] == "LabAdmin"


@pytest.mark.django_db
def test_unrolled_user_login_returns_null_role(api_client, unrolled_user):
    response = api_client.post(
        "/api/auth/login/",
        {"email": unrolled_user.email, "password": "pw-nobody"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["email"] == unrolled_user.email
    assert response.data["role"] is None


@pytest.mark.django_db
def test_login_with_bad_password_returns_401(api_client, patient_user):
    response = api_client.post(
        "/api/auth/login/",
        {"email": patient_user.email, "password": "wrong"},
        format="json",
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_me_endpoint_returns_email_and_role(api_client, physician_user):
    login = api_client.post(
        "/api/auth/login/",
        {"email": physician_user.email, "password": "pw-doc-1"},
        format="json",
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    response = api_client.get("/api/auth/me/")
    assert response.status_code == 200
    assert response.data == {"email": physician_user.email, "role": "Physician"}


@pytest.mark.django_db
def test_me_endpoint_unauthenticated_returns_401(api_client):
    response = api_client.get("/api/auth/me/")
    assert response.status_code == 401
