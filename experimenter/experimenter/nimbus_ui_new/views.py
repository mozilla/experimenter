from django.views.generic import DetailView

from experimenter.experiments.models import NimbusExperiment


class NimbusChangeLogsView(DetailView):
    model = NimbusExperiment
    context_object_name = "experiment"
    template_name = "changelog/overview.html"
