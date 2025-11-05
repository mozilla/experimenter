from django.conf import settings
from django.views.generic.edit import UpdateView

from experimenter.glean.generated.server_events import (
    create_data_collection_opt_out_server_event_logger,
)
from experimenter.glean.models import Prefs
from experimenter.glean.utils import emit_record, get_request_ip


def patch_emit_record(glean_logger):
    """Override glean's emit_record method to make writes to stdout atomic."""
    glean_logger.emit_record = emit_record
    return glean_logger


class OptOutView(UpdateView):
    model = Prefs
    fields = ["opt_out"]
    template_name = "glean/opt_out_button.html"

    data_collection_opt_out_ping = patch_emit_record(
        create_data_collection_opt_out_server_event_logger(
            application_id=settings.GLEAN_APP_ID,
            app_display_version=settings.APP_VERSION,
            channel=settings.GLEAN_APP_CHANNEL,
        )
    )

    def get_object(self, queryset=None):
        if not hasattr(self.request.user, "glean_prefs"):
            Prefs.objects.create(user=self.request.user)
        return self.request.user.glean_prefs

    def form_valid(self, form):
        if ("opt_out" in form.changed_data) and (form.cleaned_data["opt_out"] is True):
            self.data_collection_opt_out_ping.record(
                user_agent=self.request.META.get("HTTP_USER_AGENT"),
                ip_address=get_request_ip(self.request),
                nimbus_nimbus_user_id=str(self.request.user.id),
                events=[],
            )

        self.object = form.save()

        return self.render_to_response(self.get_context_data(form=self.get_form()))


class AlertDismissedView(UpdateView):
    model = Prefs
    fields = ["alert_dismissed"]
    template_name = "glean/opt_out_alert.html"

    def get_object(self, queryset=None):
        if not hasattr(self.request.user, "glean_prefs"):
            Prefs.objects.create(user=self.request.user)
        return self.request.user.glean_prefs

    def form_valid(self, form):
        self.object = form.save()
        return self.render_to_response(self.get_context_data(form=self.get_form()))
