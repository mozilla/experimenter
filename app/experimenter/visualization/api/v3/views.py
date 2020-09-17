import json

from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from experimenter.experiments.models import NimbusExperiment


def load_data_from_gcs(filename):
    return (
        json.loads(default_storage.open(filename).read())
        if default_storage.exists(filename)
        else None
    )


@api_view()
def analysis_results_view(request, slug):
    experiment = get_object_or_404(NimbusExperiment.objects.filter(slug=slug))
    experiment_data = {}

    recipe_slug = experiment.slug.replace("-", "_")

    daily_data_filename = f"""statistics_{recipe_slug}_daily.json"""
    weekly_data_filename = f"""statistics_{recipe_slug}_weekly.json"""

    daily_data = load_data_from_gcs(daily_data_filename)
    weekly_data = load_data_from_gcs(weekly_data_filename)

    if daily_data:
        experiment_data["daily"] = daily_data

    if weekly_data:
        experiment_data["weekly"] = weekly_data

    return Response(experiment_data)
