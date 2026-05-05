import hashlib
from functools import lru_cache

import boto3
from django.conf import settings


@lru_cache(maxsize=1)
def get_s3_client():
    return boto3.client(
        "s3",
        region_name=settings.AWS_S3_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def upload_report_pdf(body: bytes, *, lab_slug: str, report_id: str) -> tuple[str, str, str]:
    sha256_hex = hashlib.sha256(body).hexdigest()
    key = f"reports/{lab_slug}/{report_id}.pdf"
    bucket = settings.AWS_S3_BUCKET
    get_s3_client().put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType="application/pdf",
        Metadata={"sha256": sha256_hex},
    )
    return bucket, key, sha256_hex
