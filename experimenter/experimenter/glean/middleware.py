from django.conf import settings

from experimenter.base import app_version
from experimenter.glean.generated.server_events import (
    create_page_view_server_event_logger,
)
from experimenter.glean.models import Prefs
from experimenter.glean.utils import emit_record, get_request_ip


class GleanMiddleware:
    """
    A middleware that records page views via glean.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.page_view_ping = create_page_view_server_event_logger(
            application_id=settings.GLEAN_APP_ID,
            app_display_version=app_version(),
            channel=settings.GLEAN_APP_CHANNEL,
        )
        # override glean's emit_record method to make writes to stdout atomic
        self.page_view_ping.emit_record = emit_record

    def __call__(self, request):
        if hasattr(request, "user") and request.user.is_authenticated:
            if not hasattr(request.user, "glean_prefs"):
                Prefs.objects.create(user=request.user)
            if not request.user.glean_prefs.opt_out:
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
                    nimbus_enrollments=enrollments or [],
                    nimbus_nimbus_user_id=str(request.user.glean_prefs.nimbus_user_id),
                    url_path=request.path,
                    events=[],
                )
        return self.get_response(request)
