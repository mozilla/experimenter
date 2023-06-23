from django.views.generic import DetailView

from experimenter.experiments.models import NimbusExperiment


class NimbusChangeLogsView(DetailView):
    model = NimbusExperiment
    template_name = "changelog/overview.html"
