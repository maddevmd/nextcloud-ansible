#!/bin/sh
set -eu

export PGPASSWORD=$(cat /run/secrets/postgres_admin_password)
export NEXTCLOUD_DB_PASSWORD=$(cat /run/secrets/nextcloud_db_password)

psql -X -w -v ON_ERROR_STOP=1 \
  -h postgres -U postgres -d nextcloud <<'SQL'
\getenv app_password NEXTCLOUD_DB_PASSWORD

SELECT format(
    'CREATE ROLE nextcloud WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD %L',
    :'app_password'
)
WHERE NOT EXISTS (
    SELECT 1 FROM pg_roles WHERE rolname = 'nextcloud'
)
\gexec

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_roles
        WHERE rolname = 'nextcloud'
          AND (
              rolsuper OR rolcreatedb OR rolcreaterole
              OR rolreplication OR rolbypassrls OR NOT rolcanlogin
          )
    ) THEN
        RAISE EXCEPTION 'Unexpected privileges or login status for nextcloud';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_auth_members
        WHERE member = (
            SELECT oid FROM pg_roles WHERE rolname = 'nextcloud'
        )
    ) THEN
        RAISE EXCEPTION 'Unexpected role membership for nextcloud';
    END IF;
END
$$;

SELECT 'ALTER DATABASE nextcloud OWNER TO nextcloud'
FROM pg_database
WHERE datname = 'nextcloud'
  AND datdba <> (
      SELECT oid FROM pg_roles WHERE rolname = 'nextcloud'
  )
\gexec
SQL

PGPASSWORD="$NEXTCLOUD_DB_PASSWORD" \
  psql -X -w -v ON_ERROR_STOP=1 \
  -h postgres -U nextcloud -d nextcloud \
  -c 'SELECT current_user, current_database();'

echo "DATABASE_ACCESS_OK"
