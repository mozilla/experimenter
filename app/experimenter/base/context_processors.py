from typing import Dict

from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest


def google_analytics(request: WSGIRequest) -> Dict[str, bool]:
    """Context processor bits you need related to injecting Google Analytics
    in the rendered templates."""
    return {"USE_GOOGLE_ANALYTICS": settings.USE_GOOGLE_ANALYTICS}


def features(request: WSGIRequest) -> Dict[str, bool]:
    return {"FEATURE_MESSAGE_TYPE": settings.FEATURE_MESSAGE_TYPE}
