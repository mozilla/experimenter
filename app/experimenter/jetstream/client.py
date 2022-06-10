import json
import os
from itertools import chain

from django.conf import settings
from django.core.files.storage import default_storage

from experimenter.jetstream.models import (
    METRIC_GROUP,
    Group,
    JetstreamData,
    Metric,
    Statistic,
    create_results_object_model,
)
from experimenter.outcomes import Outcomes

BRANCH_DATA = "branch_data"
STATISTICS_FOLDER = "statistics"
METADATA_FOLDER = "metadata"


def load_data_from_gcs(path):
    if default_storage.exists(path):
        return json.loads(default_storage.open(path).read())


def get_data(slug, window):
    filename = f"statistics_{slug}_{window}.json"
    path = os.path.join(STATISTICS_FOLDER, filename)
    return load_data_from_gcs(path)


def get_metadata(slug):
    filename = f"metadata_{slug}.json"
    path = os.path.join(METADATA_FOLDER, filename)
    return load_data_from_gcs(path)


def get_results_metrics_map(
    data, primary_outcome_slugs, secondary_outcome_slugs, experiment_metadata
):
    # A mapping of metric label to relevant statistic. This is
    # used to see which statistic will be used for each metric.
    RESULTS_METRICS_MAP = {
        Metric.RETENTION: set([Statistic.BINOMIAL]),
        Metric.SEARCH: set([Statistic.MEAN]),
        Metric.DAYS_OF_USE: set([Statistic.MEAN]),
        Metric.USER_COUNT: set([Statistic.COUNT, Statistic.PERCENT]),
    }
    primary_metrics_set = set()
    primary_outcome_metrics = list(
        chain.from_iterable(
            [
                outcome.metrics
                for outcome in Outcomes.all()
                if outcome.slug in primary_outcome_slugs
            ]
        )
    )

    try:
        valid_metrics = set(
            chain.from_iterable(
                [
                    experiment_metadata["outcomes"][slug]["metrics"]
                    + experiment_metadata["outcomes"][slug]["default_metrics"]
                    for slug in experiment_metadata["outcomes"]
                ]
            )
        )
    except (TypeError, KeyError):
        # could not retrieve metadata from Jetstream
        valid_metrics = None

    for metric in primary_outcome_metrics:
        # validate against jetstream metadata unless we couldn't get it
        if valid_metrics is None or metric.slug in valid_metrics:
            RESULTS_METRICS_MAP[metric.slug] = set([Statistic.BINOMIAL])
            primary_metrics_set.add(metric.slug)

    for outcome_slug in secondary_outcome_slugs:
        RESULTS_METRICS_MAP[outcome_slug] = set([Statistic.MEAN])

    other_metrics_map, other_metrics = get_other_metrics_names_and_map(
        data, RESULTS_METRICS_MAP
    )
    RESULTS_METRICS_MAP.update(other_metrics_map)

    return RESULTS_METRICS_MAP, primary_metrics_set, other_metrics


def get_other_metrics_names_and_map(data, RESULTS_METRICS_MAP):
    # These are metrics sent from Jetstream that are not explicitly chosen
    # by users to be either primary or secondary
    other_metrics_names = {}
    other_metrics_map = {}

    # This is an ordered list of priorities of stats to graph
    priority_stats = [Statistic.MEAN, Statistic.BINOMIAL]
    other_data = [
        data_point for data_point in data if data_point.metric not in RESULTS_METRICS_MAP
    ]
    for jetstream_data_point in other_data:
        metric = jetstream_data_point.metric
        statistic = jetstream_data_point.statistic

        if statistic in priority_stats:
            metric_title = " ".join([word.title() for word in metric.split("_")])
            group_name = METRIC_GROUP.get(metric, Group.OTHER)
            if group_name not in other_metrics_names:
                other_metrics_names[group_name] = {}
            other_metrics_names[group_name][metric] = metric_title

            if metric not in other_metrics_map or priority_stats.index(
                statistic
            ) < priority_stats.index(other_metrics_map[metric]):
                other_metrics_map[metric] = statistic

    # Turn other_metrics_map into the format needed
    # by get_result_metrics_map()
    other_metrics_map = {k: set([v]) for k, v in other_metrics_map.items()}

    return other_metrics_map, other_metrics_names


def get_experiment_data(experiment):
    recipe_slug = experiment.slug.replace("-", "_")
    windows = ["daily", "weekly", "overall"]
    raw_data = {}

    experiment_metadata = get_metadata(recipe_slug)

    experiment_data = {
        "show_analysis": settings.FEATURE_ANALYSIS,
        "metadata": experiment_metadata,
    }

    for window in windows:
        data = raw_data[window] = JetstreamData(
            __root__=(get_data(recipe_slug, window) or [])
        )
        result_metrics, primary_metrics_set, other_metrics = get_results_metrics_map(
            data,
            experiment.primary_outcomes,
            experiment.secondary_outcomes,
            experiment_metadata,
        )

        if data and window == "overall":
            # Append some values onto Jetstream data
            data.append_population_percentages()
            data.append_retention_data(raw_data["weekly"])

            ResultsObjectModel = create_results_object_model(data)
            data = ResultsObjectModel(result_metrics, data, experiment)
            data.append_conversion_count(primary_metrics_set)

            experiment_data["other_metrics"] = other_metrics
        elif data and window == "weekly":
            ResultsObjectModel = create_results_object_model(data)
            data = ResultsObjectModel(result_metrics, data, experiment, window)

        transformed_data = data.dict(exclude_none=True) or None

        experiment_data[window] = transformed_data

    return experiment_data
