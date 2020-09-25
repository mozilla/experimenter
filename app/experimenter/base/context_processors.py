from django.conf import settings


def google_analytics(request):
    """Context processor bits you need related to injecting Google Analytics
    in the rendered templates."""
    return {"USE_GOOGLE_ANALYTICS": settings.USE_GOOGLE_ANALYTICS}


def features(request):
    return {
        "FEATURE_MESSAGE_TYPE": settings.FEATURE_MESSAGE_TYPE,
        "FEATURE_ANALYSIS": settings.FEATURE_ANALYSIS,
        "SENTRY_DSN": settings.SENTRY_DSN,
    }
