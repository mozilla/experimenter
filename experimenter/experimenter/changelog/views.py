from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from experimenter.experiments.models import NimbusExperiment


class NimbusChangeLogsView(DetailView):
    model = NimbusExperiment
    template_name = "changelog/changelogs_overview.html"
    context_object_name = "experiment"

    def get_object(self, queryset=None):
        slug = self.kwargs.get("slug")
        experiment = get_object_or_404(NimbusExperiment, slug=slug)
        return experiment

    def get_context_data(self, **kwargs):
        slug = self.kwargs.get("slug")
        context = super().get_context_data(**kwargs)
        experiment = self.get_object()

        changelogs = list(experiment.changes.all())

        context["slug"] = slug
        context["changelogs"] = changelogs
        context["experiment"] = experiment
        return context
