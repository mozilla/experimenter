from django.conf import settings


def google_analytics(request):
    """Context processor bits you need related to injecting Google Analytics
    in the rendered templates."""
    return {"USE_GOOGLE_ANALYTICS": settings.USE_GOOGLE_ANALYTICS}
