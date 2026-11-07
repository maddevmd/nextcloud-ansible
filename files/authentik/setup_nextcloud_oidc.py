import json
import sys

from django.db import transaction

from authentik.core.models import Application
from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow
from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping


config = json.load(sys.stdin)

if not config["client_secret"].strip():
    raise RuntimeError("OIDC client secret is empty")


def apply_fields(obj, values):
    changed = False

    for field, value in values.items():
        if getattr(obj, field) != value:
            setattr(obj, field, value)
            changed = True

    if changed:
        obj.save()

    return changed


with transaction.atomic():
    authorization_flow = Flow.objects.get(
        slug="default-provider-authorization-explicit-consent"
    )
    invalidation_flow = Flow.objects.get(
        slug="default-provider-invalidation-flow"
    )
    signing_key = CertificateKeyPair.objects.get(
        name="authentik Internal JWT Certificate"
    )

    provider_values = {
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "client_type": "confidential",
        "authorization_flow": authorization_flow,
        "invalidation_flow": invalidation_flow,
        "signing_key": signing_key,
        "sub_mode": "user_uuid",
        "grant_types": ["authorization_code", "refresh_token"],
        "logout_method": "backchannel",
        "logout_uri": (
            config["nextcloud_url"]
            + "/apps/user_oidc/backchannel-logout/authentik"
        ),
        "_redirect_uris": [
            {
                "matching_mode": "strict",
                "redirect_uri_type": "authorization",
                "url": config["redirect_uri"],
            }
        ],
    }

    provider, created = OAuth2Provider.objects.get_or_create(
        name="Nextcloud OIDC",
        defaults=provider_values,
    )
    changed = created
    changed = apply_fields(provider, provider_values) or changed

    scopes = [
        ScopeMapping.objects.get(
            managed=f"goauthentik.io/providers/oauth2/scope-{name}"
        )
        for name in ["openid", "email", "profile"]
    ]

    group_mapping_values = {
        "scope_name": "nextcloud_groups",
        "expression": (
            'return {"nextcloud_groups": '
            'list(request.user.groups.filter('
            'name__in=["nextcloud-users"]'
            ').values_list("name", flat=True))}'
        ),
    }

    group_mapping, created = ScopeMapping.objects.get_or_create(
        name="Nextcloud selected groups",
        defaults=group_mapping_values,
    )
    changed = created or changed
    changed = apply_fields(group_mapping, group_mapping_values) or changed

    scopes.append(group_mapping)

    current_scopes = set(
        provider.property_mappings.values_list("pk", flat=True)
    )
    desired_scopes = {scope.pk for scope in scopes}

    if current_scopes != desired_scopes:
        provider.property_mappings.set(scopes)
        changed = True

    application_values = {
        "name": "Nextcloud",
        "provider_id": provider.pk,
        "meta_launch_url": config["nextcloud_url"],
    }

    application, created = Application.objects.get_or_create(
        slug=config["slug"],
        defaults=application_values,
    )
    changed = created or changed
    changed = apply_fields(application, application_values) or changed

print("OIDC_CHANGED" if changed else "OIDC_UNCHANGED")
