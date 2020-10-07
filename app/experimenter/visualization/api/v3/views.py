import json

from django.conf import settings
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from experimenter.experiments.models import NimbusExperiment

# This is the metric label for rows that contain user counts.
USER_COUNTS_KEY = "identity"


def load_data_from_gcs(filename):
    return (
        json.loads(default_storage.open(filename).read())
        if default_storage.exists(filename)
        else None
    )


def get_results_metrics_map(features):
    # A mapping of metric label to relevant statistic. This is
    # used to see which statistic will be used for each metric.
    RESULTS_METRICS_MAP = {
        "retained": "binomial",
        "search_count": "mean",
        "identity": "count",
    }
    for feature in features:
        feature_metric_id = f"{feature}_ever_used"
        RESULTS_METRICS_MAP[feature_metric_id] = "binomial"

    return RESULTS_METRICS_MAP


def append_population_percentages(data):
    total_population = 0
    branches = {}
    for row in data:
        if row["metric"] == USER_COUNTS_KEY:
            total_population += row["point"]
            branches[row["branch"]] = row["point"]

    for branch_name, branch_user_count in sorted(branches.items()):
        data.append(
            {
                "metric": "identity",
                "statistic": "percentage",
                "branch": branch_name,
                "point": round(branch_user_count / total_population * 100),
            }
        )


def get_data(slug, window):
    filename = f"""statistics_{slug}_{window}.json"""
    data = load_data_from_gcs(filename)
    return data


@api_view()
def analysis_results_view(request, slug):
    windows = ["daily", "weekly", "overall"]

    experiment = get_object_or_404(NimbusExperiment.objects.filter(slug=slug))
    experiment_data = {"show_analysis": settings.FEATURE_ANALYSIS}
    recipe_slug = experiment.slug.replace("-", "_")

    for window in windows:
        data = get_data(recipe_slug, window)
        if data and window == "overall":
            append_population_percentages(data)
        experiment_data[window] = data
    experiment_data["result_map"] = get_results_metrics_map(experiment.features)

    return Response(experiment_data)
