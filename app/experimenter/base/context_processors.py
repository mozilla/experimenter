import json
import urllib

from django.conf import settings
from django.urls import reverse


def google_analytics(request):
    """Context processor bits you need related to injecting Google Analytics
    in the rendered templates."""
    return {"USE_GOOGLE_ANALYTICS": settings.USE_GOOGLE_ANALYTICS}


def features(request):
    return {
        "FEATURE_MESSAGE_TYPE": settings.FEATURE_MESSAGE_TYPE,
        "FEATURE_ANALYSIS": settings.FEATURE_ANALYSIS,
        "APP_CONFIG": urllib.parse.quote(
            json.dumps(
                {
                    "sentry_dsn": settings.SENTRY_DSN_NIMBUS_UI,
                    "graphql_url": reverse("nimbus-api-graphql"),
                }
            )
        ),
    }


def debug(request):
    return {"DEBUG": settings.DEBUG}
