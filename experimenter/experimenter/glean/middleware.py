from django.conf import settings
from glean import Glean, load_metrics


class GleanMiddleware:
    """
    A middleware that records page views via glean.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.metrics = glean.load_metrics(
            settings.BASE_DIR / "telemetry" / "metrics.yaml"
        )
        Glean.set_collection_enabled(settings.ENABLE_GLEAN)

    def __call__(self, request):
        self.metrics.page.view.record(
            self.metrics.page.ViewExtra(
                path=request.path,
                nimbus_user_id=(request.user.id if hasattr(request, "user") else None),
            )
        )
        return self.get_response(request)
