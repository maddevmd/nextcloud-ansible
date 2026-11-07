#!/bin/sh
set -eu

admin_password=$(cat /run/secrets/minio_root_password)
nextcloud_secret=$(cat /run/secrets/nextcloud_s3_secret_key)

mc alias set storage \
  http://minio:9000 \
  nextcloud-storage-admin \
  "$admin_password" >/dev/null

mc admin policy create \
  storage \
  nextcloud-only \
  /work/nextcloud-policy.json

mc admin user add \
  storage \
  nextcloud \
  "$nextcloud_secret"

mc admin policy attach \
  storage \
  nextcloud-only \
  --user nextcloud

echo "Nextcloud account configured"
