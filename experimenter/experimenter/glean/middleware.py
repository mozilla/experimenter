from django.conf import settings
from glean import Glean, load_metrics, load_pings


class GleanMiddleware:
    """
    A middleware that records page views via glean.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.metrics = load_metrics(settings.BASE_DIR / "telemetry" / "metrics.yaml")
        self.pings = load_pings(settings.BASE_DIR / "telemetry" / "pings.yaml")
        Glean.set_collection_enabled(settings.ENABLE_GLEAN)

    def __call__(self, request):
        self.metrics.url.path.set(request.path)
        if hasattr(request, "user"):
            self.metrics.nimbus.nimbus_user_id.set(str(request.user.id))
        if request.cirrus and request.cirrus.enrollments:
            self.metrics.nimbus.enrollments.set(
                [
                    {**enrollment, "is_preview": enrollment.get("is_preview") == "true"}
                    for enrollment in request.cirrus.enrollments
                ]
            )
        self.pings.page_view.submit()
        return self.get_response(request)
