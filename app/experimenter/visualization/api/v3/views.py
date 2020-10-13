import json
from enum import IntEnum

from django.conf import settings
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from experimenter.experiments.models import NimbusExperiment


class Significance(IntEnum):
    POSITIVE = 0
    NEGATIVE = 1
    NEUTRAL = 2


class BranchComparison:
    ABSOLUTE = "absolute"
    DIFFERENCE = "difference"
    UPLIFT = "relative_uplift"


class Metric:
    RETENTION = "retained"
    SEARCH = "search_count"
    USER_COUNT = "identity"


class Statistic:
    PERCENT = "percentage"
    BINOMIAL = "binomial"
    MEAN = "mean"
    COUNT = "count"


BRANCH_DATA = "branch_data"


def load_data_from_gcs(filename):
    return (
        json.loads(default_storage.open(filename).read())
        if default_storage.exists(filename)
        else None
    )


def get_results_metrics_map(probe_sets):
    # A mapping of metric label to relevant statistic. This is
    # used to see which statistic will be used for each metric.
    RESULTS_METRICS_MAP = {
        Metric.RETENTION: set([Statistic.BINOMIAL]),
        Metric.SEARCH: set([Statistic.MEAN]),
        Metric.USER_COUNT: set([Statistic.COUNT, Statistic.PERCENT]),
    }
    for probe_set in probe_sets:
        probe_set_id = f"{probe_set}_ever_used"
        RESULTS_METRICS_MAP[probe_set_id] = set([Statistic.BINOMIAL])
    return RESULTS_METRICS_MAP


def append_population_percentages(data):
    total_population = 0
    branches = {}
    for row in data:
        if row["metric"] == Metric.USER_COUNT:
            total_population += row["point"]
            branches[row["branch"]] = row["point"]

    for branch_name, branch_user_count in sorted(branches.items()):
        data.append(
            {
                "metric": Metric.USER_COUNT,
                "statistic": Statistic.PERCENT,
                "branch": branch_name,
                "point": round(branch_user_count / total_population * 100),
            }
        )


def computeSignificance(lower, upper):
    if max(lower, upper, 0) == 0:
        return Significance.NEGATIVE
    if min(lower, upper, 0) == 0:
        return Significance.POSITIVE
    else:
        return Significance.NEUTRAL


def process_data_for_consumption(data, experiment):
    results = {}
    for row in data:
        branch = row.get("branch")
        metric = row.get("metric")
        lower = row.get("lower")
        upper = row.get("upper")
        point = row.get("point")
        statistic = row.get("statistic")

        results[branch] = results.get(
            branch,
            {"is_control": experiment.control_branch.name == branch, BRANCH_DATA: {}},
        )

        resultMetrics = get_results_metrics_map(experiment.probe_sets.all())
        if metric in resultMetrics and statistic in resultMetrics[metric]:
            results[branch][BRANCH_DATA][metric] = results[branch][BRANCH_DATA].get(
                metric,
                {
                    BranchComparison.ABSOLUTE: {},
                    BranchComparison.DIFFERENCE: {},
                    BranchComparison.UPLIFT: {},
                },
            )

            if metric == Metric.USER_COUNT and statistic == Statistic.PERCENT:
                results[branch][BRANCH_DATA][Metric.USER_COUNT]["percent"] = point
                continue

            comparison = row.get("comparison", BranchComparison.ABSOLUTE)
            if comparison == BranchComparison.DIFFERENCE and lower and upper:
                results[branch][BRANCH_DATA][metric].update(
                    {"significance": computeSignificance(lower, upper)}
                )

            results[branch][BRANCH_DATA][metric][comparison].update(
                {"lower": lower, "upper": upper, "point": point}
            )
    return results


def get_data(slug, window, experiment):
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
        data = get_data(recipe_slug, window, experiment)

        if data and window == "overall":
            append_population_percentages(data)
            data = process_data_for_consumption(data, experiment)

        experiment_data[window] = data

    return Response(experiment_data)
