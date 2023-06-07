from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from experimenter.experiments.models import NimbusChangeLog, NimbusExperiment


class NimbusChangeLogsView(DetailView):
    model = NimbusChangeLog
    context_object_name = "experiment"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def get_object(self, queryset=None):
        slug = self.kwargs.get("slug")
        experiment = get_object_or_404(NimbusExperiment, slug=slug)
        return experiment

    def get_context_data(self, **kwargs):
        slug = self.kwargs.get("slug")
        context = super().get_context_data(**kwargs)
        experiment = self.object

        # Retrieve the changelogs for the experiment
        changelogs = experiment.changes.all()

        context["slug"] = slug
        context["changelogs"] = changelogs
        return context

    def render_to_response(
        self, context, **response_kwargs
    ):  # rendering simple text until templates are implemented
        return HttpResponse("test")
