import json
import subprocess
from pathlib import Path


def run_mc(*args):
    result = subprocess.run(
        ["mc", "--json", *args],
        capture_output=True,
        text=True,
    )

    lines = [line for line in result.stdout.splitlines() if line.strip()]

    if not lines:
        raise RuntimeError("mc returned no JSON response")

    response = json.loads(lines[-1])
    return result.returncode, response


def normalize(policy):
    result = dict(policy)
    statements = []

    for original in result.get("Statement", []):
        statement = dict(original)

        for field in ("Action", "Resource"):
            if field in statement:
                values = statement[field]
                if isinstance(values, str):
                    values = [values]
                statement[field] = sorted(values)

        statements.append(statement)

    result["Statement"] = sorted(
        statements,
        key=lambda value: json.dumps(value, sort_keys=True),
    )

    return result


password = Path("/run/secrets/minio_root_password").read_text().strip()

code, _ = run_mc(
    "alias", "set", "storage",
    "http://minio:9000",
    "nextcloud-storage-admin",
    password,
)

if code != 0:
    raise RuntimeError("Cannot configure administrative connection")

desired = json.loads(Path("/work/nextcloud-policy.json").read_text())

code, response = run_mc(
    "admin", "policy", "info", "storage", "nextcloud-only",
)

if code == 0:
    actual = response["policyInfo"]["Policy"]
    needs_update = normalize(actual) != normalize(desired)
else:
    error_code = response.get("error", {}).get("cause", {}).get("error", {}).get("Code")

    if error_code not in ("XMinioAdminNoSuchPolicy", "NoSuchPolicy"):
        raise RuntimeError(
            f"Cannot inspect policy; error code: {error_code}"
        )

    needs_update = True

if needs_update:
    code, _ = run_mc(
        "admin", "policy", "create",
        "storage", "nextcloud-only",
        "/work/nextcloud-policy.json",
    )

    if code != 0:
        raise RuntimeError("Cannot create or update policy")

    print("POLICY_CHANGED")
else:
    print("POLICY_UNCHANGED")
