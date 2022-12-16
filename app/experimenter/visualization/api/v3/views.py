from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from experimenter.experiments.models import NimbusExperiment


@api_view()
def analysis_results_view(request, slug):
    experiment = get_object_or_404(NimbusExperiment.objects.filter(slug=slug))
    if experiment.results_data is not None and "v2" in experiment.results_data:
        return Response(experiment.results_data["v2"])

    return Response(None)
