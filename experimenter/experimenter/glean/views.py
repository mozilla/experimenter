import glean
from django.conf import settings
from django.views.generic.edit import UpdateView

from experimenter.glean.models import Prefs
from experimenter.glean.server_events import (
    create_data_collection_opt_out_server_event_logger,
)
from experimenter.glean.utils import get_request_ip


class OptOutView(UpdateView):
    model = Prefs
    fields = ["opt_out"]
    template_name = "glean/opt_out_button.html"

    data_collection_opt_out_ping = create_data_collection_opt_out_server_event_logger(
        application_id=settings.GLEAN_APP_ID,
        app_display_version=settings.APP_VERSION,
        channel=settings.GLEAN_APP_CHANNEL,
    )
    metrics = glean.load_metrics(settings.BASE_DIR / "telemetry" / "metrics.yaml")
    pings = glean.load_pings(settings.BASE_DIR / "telemetry" / "pings.yaml")

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
