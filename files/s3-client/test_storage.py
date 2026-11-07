import sys
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

bucket = "lab-s3-test"
key = "persistence-check.txt"
expected = b"Data must survive container recreation.\n"

if len(sys.argv) != 2 or sys.argv[1] not in ("write", "read"):
    raise SystemExit("Usage: test_storage.py write|read")

if sys.argv[1] == "write":
    try:
        s3.head_bucket(Bucket=bucket)
    except ClientError as error:
        if error.response["ResponseMetadata"]["HTTPStatusCode"] != 404:
            raise
        s3.create_bucket(Bucket=bucket)

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=expected,
        ContentType="text/plain",
    )
    print("Test object written")

response = s3.get_object(Bucket=bucket, Key=key)
actual = response["Body"].read()

if actual != expected:
    raise SystemExit("ERROR: object content differs")

print("Object read successfully; content matches")
