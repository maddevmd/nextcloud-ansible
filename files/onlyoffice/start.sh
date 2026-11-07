#!/bin/sh
set -eu

JWT_SECRET=$(cat /run/secrets/onlyoffice_jwt_secret)
export JWT_SECRET

if [ -z "$JWT_SECRET" ]; then
    echo "ONLYOFFICE JWT secret is empty" >&2
    exit 1
fi

exec /app/ds/run-document-server.sh "$@"
