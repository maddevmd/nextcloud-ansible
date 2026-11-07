from pathlib import Path
from uuid import uuid4

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


secret = Path("/run/secrets/nextcloud_s3_secret_key").read_text().strip()

s3 = boto3.client(
    "s3",
    endpoint_url="http://minio:9000",
    aws_access_key_id="nextcloud",
    aws_secret_access_key=secret,
    region_name="us-east-1",
    config=Config(
        signature_version="s3v4",
        s3={"addressing_style": "path"},
        connect_timeout=5,
        read_timeout=10,
    ),
)

bucket = "nextcloud"
key = f"access-check-{uuid4().hex}.txt"
data = b"Nextcloud S3 access check\n"

# Проверяем разрешённые операции.
s3.head_bucket(Bucket=bucket)
s3.list_objects_v2(Bucket=bucket, MaxKeys=1)
print("OK: own bucket is accessible")

s3.put_object(Bucket=bucket, Key=key, Body=data)

try:
    response = s3.get_object(Bucket=bucket, Key=key)
    body = response["Body"]

    try:
        actual = body.read()
    finally:
        body.close()

    if actual != data:
        raise RuntimeError("Object content differs")

    print("OK: write and read allowed")
finally:
    s3.delete_object(Bucket=bucket, Key=key)

print("OK: test object deleted")


def expect_denied(description, operation):
    try:
        operation()
    except ClientError as error:
        code = error.response["Error"]["Code"]
        status = error.response["ResponseMetadata"]["HTTPStatusCode"]

        if status == 403 and code == "AccessDenied":
            print(f"OK: {description} denied")
        else:
            raise
    else:
        raise RuntimeError(f"Unexpected permission: {description}")


# Проверяем запрещённые операции.
expect_denied(
    "listing another bucket",
    lambda: s3.list_objects_v2(Bucket="lab-s3-test", MaxKeys=1),
)

expect_denied(
    "reading another bucket",
    lambda: s3.get_object(
        Bucket="lab-s3-test",
        Key="persistence-check.txt",
    ),
)

expect_denied(
    "writing another bucket",
    lambda: s3.put_object(
        Bucket="lab-s3-test",
        Key=key,
        Body=data,
    ),
)

print("PASS: Nextcloud bucket permissions verified")
