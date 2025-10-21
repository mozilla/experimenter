import glean
from django.conf import settings


class GleanMiddleware:
    """
    A middleware that records page views via glean.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.metrics = glean.load_metrics(
            settings.BASE_DIR / "telemetry" / "metrics.yaml"
        )
        self.pings = glean.load_pings(settings.BASE_DIR / "telemetry" / "pings.yaml")
        glean.Glean.initialize(
            application_id="experimenter-backend",
            application_version=settings.APP_VERSION,
            data_dir=settings.GLEAN_DATA_DIR,
            upload_enabled=settings.GLEAN_UPLOAD_ENABLED,
            configuration=glean.Configuration(),
        )

    def __call__(self, request):
        if (
            hasattr(request, "user")
            and request.user.is_authenticated
            and not (
                hasattr(request.user, "glean_prefs") and request.user.glean_prefs.opt_out
            )
        ):
            self.metrics.url.path.set(request.path)
            self.metrics.nimbus.nimbus_user_id.set(str(request.user.id))
            if request.cirrus and request.cirrus.enrollments:
                self.metrics.nimbus.enrollments.set(
                    [
                        {
                            **enrollment,
                            "is_preview": enrollment.get("is_preview") == "true",
                        }
                        for enrollment in request.cirrus.enrollments
                    ]
                )
            self.pings.page_view.submit()
        return self.get_response(request)
