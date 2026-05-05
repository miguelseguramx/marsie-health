import boto3
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from moto import mock_aws

from apps.labs import s3 as s3_module


@pytest.fixture
def s3_bucket(settings):
    settings.AWS_S3_BUCKET = "test-bucket"
    settings.AWS_S3_REGION = "us-east-1"
    settings.AWS_ACCESS_KEY_ID = "test"
    settings.AWS_SECRET_ACCESS_KEY = "test"
    s3_module.get_s3_client.cache_clear()
    with mock_aws():
        boto3.client("s3", region_name="us-east-1").create_bucket(Bucket="test-bucket")
        yield "test-bucket"
    s3_module.get_s3_client.cache_clear()


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
