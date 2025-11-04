from django.conf import settings

from experimenter.glean.generated.server_events import (
    create_page_view_server_event_logger,
)
from experimenter.glean.utils import get_request_ip


class GleanMiddleware:
    """
    A middleware that records page views via glean.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.page_view_ping = create_page_view_server_event_logger(
            application_id=settings.GLEAN_APP_ID,
            app_display_version=settings.APP_VERSION,
            channel=settings.GLEAN_APP_CHANNEL,
        )

    def __call__(self, request):
        if (
            hasattr(request, "user")
            and request.user.is_authenticated
            and not (
                hasattr(request.user, "glean_prefs") and request.user.glean_prefs.opt_out
            )
        ):
            enrollments = None
            if request.cirrus and request.cirrus.enrollments:
                enrollments = [
                    {
                        **enrollment,
                        "is_preview": enrollment.get("is_preview") == "true",
                    }
                    for enrollment in request.cirrus.enrollments
                ]
            self.page_view_ping.record(
                user_agent=request.META.get("HTTP_USER_AGENT"),
                ip_address=get_request_ip(request),
                nimbus_enrollments=enrollments,
                nimbus_nimbus_user_id=str(request.user.id),
                url_path=request.path,
                events=[],
            )
        return self.get_response(request)
