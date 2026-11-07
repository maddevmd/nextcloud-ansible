import os
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


password = Path("/run/secrets/minio_root_password").read_text().strip()

s3 = boto3.client(
    "s3",
    endpoint_url="http://minio:9000",
    aws_access_key_id="nextcloud-storage-admin",
    aws_secret_access_key=password,
    region_name="us-east-1",
    config=Config(
        signature_version="s3v4",
        s3={"addressing_style": "path"},
        connect_timeout=5,
        read_timeout=10,
    ),
)

bucket = os.environ.get("S3_BUCKET", "nextcloud")

try:
    s3.head_bucket(Bucket=bucket)
    print(f"Bucket {bucket} already exists")
except ClientError as error:
    status = error.response["ResponseMetadata"]["HTTPStatusCode"]

    if status != 404:
        raise

    s3.create_bucket(Bucket=bucket)
    print(f"Bucket {bucket} created")

s3.head_bucket(Bucket=bucket)
print("Bucket is accessible")
