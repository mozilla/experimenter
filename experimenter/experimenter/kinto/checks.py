from django.conf import settings
from django.core.checks import Error

from experimenter.kinto.client import KintoClient


def remote_settings_check(app_configs, **kwargs):
    errors = []

    client = KintoClient(settings.KINTO_COLLECTION_NIMBUS_PREVIEW)

    try:
        client.heartbeat()
    except Exception as e:
        errors.append(
            Error(
                f"Remote Settings connection is unhealthy: {e}",
                hint="Verify connectivity and server status.",
                id="experimenter.remotesettings.E001",
            )
        )

    if not errors and not client.authenticated():
        errors.append(
            Error(
                "Invalid credentials for Remote Settings",
                hint="Contact administrators.",
                id="experimenter.remotesettings.E002",
            )
        )

    return errors
