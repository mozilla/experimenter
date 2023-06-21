from django.views.generic import DetailView

from experimenter.experiments.models import NimbusExperiment


class NimbusChangeLogsView(DetailView):
    model = NimbusExperiment
    template_name = "changelog/overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["changelogs"] = list(self.object.changes.all())
        return context
