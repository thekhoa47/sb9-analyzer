# app/storage/r2.py
import boto3
from app.core.config import settings

_s3 = boto3.client(
    "s3",
    endpoint_url=settings.R2_S3_ENDPOINT,
    aws_access_key_id=settings.R2_ACCESS_KEY_ID,
    aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
)


def upload_bytes_and_get_url(
    key: str, data: bytes, content_type: str = "image/svg+xml"
) -> str:
    _s3.put_object(
        Bucket=settings.R2_BUCKET, Key=key, Body=data, ContentType=content_type
    )
    return f"{settings.R2_PUBLIC_BASE}/{key}"
