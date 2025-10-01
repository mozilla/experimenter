import glean
from django.conf import settings
from django.views.generic.edit import UpdateView

from experimenter.glean.models import Prefs


class OptOutView(UpdateView):
    model = Prefs
    fields = ["opt_out"]
    template_name = "glean/opt_out_button.html"

    metrics = glean.load_metrics(settings.BASE_DIR / "telemetry" / "metrics.yaml")

    def get_object(self, queryset=None):
        if not hasattr(self.request.user, "glean_prefs"):
            Prefs.objects.create(user=self.request.user)
        return self.request.user.glean_prefs

    def form_valid(self, form):
        if ("opt_out" in form.changed_data) and (form.cleaned_data["opt_out"] is True):
            self.metrics.data_collection.opt_out.record(
                self.metrics.data_collection.OptOutExtra(
                    nimbus_user_id=str(self.request.user.id),
                )
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
