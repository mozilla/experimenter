from typing import Dict

from django.conf import settings
from django.http import HttpRequest


def google_analytics(request: HttpRequest) -> Dict[str, bool]:
    """Context processor bits you need related to injecting Google Analytics
    in the rendered templates."""
    return {"USE_GOOGLE_ANALYTICS": settings.USE_GOOGLE_ANALYTICS}


def features(request: HttpRequest) -> Dict[str, bool]:
    return {"FEATURE_MESSAGE_TYPE": settings.FEATURE_MESSAGE_TYPE}
