# app/storage/r2.py
import os
import boto3
from dotenv import load_dotenv

load_dotenv()

R2_S3_ENDPOINT = os.environ[
    "R2_S3_ENDPOINT"
]  # https://<ACCOUNT_ID>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID = os.environ["R2_ACCESS_KEY_ID"]
R2_SECRET_ACCESS_KEY = os.environ["R2_SECRET_ACCESS_KEY"]
R2_BUCKET = os.environ["R2_BUCKET"]
R2_PUBLIC_BASE = os.environ["R2_PUBLIC_BASE"]  # https://<bucket>.r2.dev

_s3 = boto3.client(
    "s3",
    endpoint_url=R2_S3_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
)


def upload_bytes_and_get_url(
    key: str, data: bytes, content_type: str = "image/png"
) -> str:
    _s3.put_object(Bucket=R2_BUCKET, Key=key, Body=data, ContentType=content_type)
    return f"{R2_PUBLIC_BASE}/{key}"
