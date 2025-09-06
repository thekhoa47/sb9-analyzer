# app/ml/model_store.py
import os
import pathlib
import boto3
from botocore.client import Config

# Local cache dir (survives process restarts if using persistent disk)
CACHE_DIR = pathlib.Path(os.getenv("MODEL_CACHE_DIR", "app/.cache/models"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def r2_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ[
            "R2_ENDPOINT_URL"
        ],  # e.g. https://<accountid>.r2.cloudflarestorage.com
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def download_if_needed(bucket: str, key: str) -> str:
    """
    Download the object if it is missing or ETag changed. Returns local path.
    """
    s3 = r2_client()
    head = s3.head_object(Bucket=bucket, Key=key)
    etag = head["ETag"].strip('"')

    local_path = CACHE_DIR / key
    local_path.parent.mkdir(parents=True, exist_ok=True)
    etag_path = local_path.with_suffix(local_path.suffix + ".etag")

    if local_path.exists() and etag_path.exists():
        if etag_path.read_text().strip() == etag:
            return str(local_path)

    # fetch
    s3.download_file(bucket, key, str(local_path))
    etag_path.write_text(etag)
    return str(local_path)
