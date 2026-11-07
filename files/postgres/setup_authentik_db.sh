#!/bin/sh
set -eu

PGPASSWORD=$(cat /run/secrets/postgres_admin_password)
AUTHENTIK_DB_PASSWORD=$(cat /run/secrets/authentik_db_password)
export PGPASSWORD AUTHENTIK_DB_PASSWORD

psql -X -w -v ON_ERROR_STOP=1 \
  -h postgres -U postgres -d postgres <<'SQL'
\getenv app_password AUTHENTIK_DB_PASSWORD

SELECT format(
    'CREATE ROLE authentik WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD %L',
    :'app_password'
)
WHERE NOT EXISTS (
    SELECT 1 FROM pg_roles WHERE rolname = 'authentik'
)
\gexec

SELECT 'CREATE DATABASE authentik OWNER authentik'
WHERE NOT EXISTS (
    SELECT 1 FROM pg_database WHERE datname = 'authentik'
)
\gexec

SELECT 'ALTER DATABASE authentik OWNER TO authentik'
FROM pg_database
WHERE datname = 'authentik'
  AND datdba <> (
      SELECT oid FROM pg_roles WHERE rolname = 'authentik'
  )
\gexec
SQL

PGPASSWORD="$AUTHENTIK_DB_PASSWORD" \
  psql -X -w -v ON_ERROR_STOP=1 \
  -h postgres -U authentik -d authentik \
  -c 'SELECT current_user, current_database();'

echo "AUTHENTIK_DATABASE_ACCESS_OK"
