# test_r2.py
import os, boto3
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()  # loads backend/.env

endpoint = os.environ["R2_S3_ENDPOINT"]
bucket = os.environ["R2_BUCKET"]
ak = os.environ["R2_ACCESS_KEY_ID"]
sk = os.environ["R2_SECRET_ACCESS_KEY"]
public_base = os.environ["R2_PUBLIC_BASE"]

s3 = boto3.client(
    "s3",
    endpoint_url=endpoint,
    aws_access_key_id=ak,
    aws_secret_access_key=sk,
    config=Config(signature_version="s3v4"),
)

key = "health/check.txt"
s3.put_object(Bucket=bucket, Key=key, Body=b"hello r2", ContentType="text/plain")
print("Public URL:", f"{public_base}/{key}")