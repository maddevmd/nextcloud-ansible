import json
import subprocess
from pathlib import Path


def run_mc(*args):
    result = subprocess.run(
        ["mc", "--json", *args],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "mc command failed; check MinIO connectivity and permissions"
        )

    responses = [
        json.loads(line)
        for line in result.stdout.splitlines()
        if line.strip()
    ]

    if any(item.get("status") == "error" for item in responses):
        raise RuntimeError("mc returned an error")

    return responses


admin_password = Path(
    "/run/secrets/minio_root_password"
).read_text().strip()

nextcloud_secret = Path(
    "/run/secrets/nextcloud_s3_secret_key"
).read_text().strip()

run_mc(
    "alias", "set", "storage",
    "http://minio:9000",
    "nextcloud-storage-admin",
    admin_password,
)

users = run_mc("admin", "user", "list", "storage")

user = next(
    (item for item in users if item.get("accessKey") == "nextcloud"),
    None,
)

changed = False

if user is None:
    run_mc(
        "admin", "user", "add",
        "storage", "nextcloud", nextcloud_secret,
    )
    changed = True

    user = run_mc(
        "admin", "user", "info", "storage", "nextcloud"
    )[-1]

if user.get("userStatus") != "enabled":
    raise RuntimeError(
        "Nextcloud account is disabled; investigate before enabling it"
    )

if user.get("memberOf"):
    raise RuntimeError(
        "Unexpected group membership; review inherited permissions"
    )

policies = {
    name.strip()
    for name in user.get("policyName", "").split(",")
    if name.strip()
}

if policies - {"nextcloud-only"}:
    raise RuntimeError(
        "Unexpected additional policies; review permissions"
    )

if "nextcloud-only" not in policies:
    run_mc(
        "admin", "policy", "attach",
        "storage", "nextcloud-only",
        "--user", "nextcloud",
    )
    changed = True

print("USER_CHANGED" if changed else "USER_UNCHANGED")
