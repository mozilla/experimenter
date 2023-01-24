import json
import os
from collections import defaultdict
from itertools import chain

from django.conf import settings
from django.core.files.storage import default_storage

from experimenter.jetstream.models import (
    METRIC_GROUP,
    AnalysisBasis,
    Group,
    JetstreamData,
    Metric,
    Segment,
    Statistic,
    create_results_object_model,
)
from experimenter.outcomes import Outcomes

BRANCH_DATA = "branch_data"
STATISTICS_FOLDER = "statistics"
METADATA_FOLDER = "metadata"
ERRORS_FOLDER = "errors"
ALL_STATISTICS = {
    Statistic.BINOMIAL,
    Statistic.MEAN,
    Statistic.COUNT,
    Statistic.PERCENT,
}


class AnalysisWindow:
    DAILY = "daily"
    WEEKLY = "weekly"
    OVERALL = "overall"


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


def get_analysis_errors(slug):
    filename = f"errors_{slug}.json"
    path = os.path.join(ERRORS_FOLDER, filename)
    return load_data_from_gcs(path)


def get_results_metrics_map(
    data, primary_outcome_slugs, secondary_outcome_slugs, outcomes_metadata
):
    # A mapping of metric label to relevant statistic. This is
    # used to see which statistic will be used for each metric.
    RESULTS_METRICS_MAP = {
        Metric.RETENTION: {Statistic.BINOMIAL},
        Metric.SEARCH: {Statistic.MEAN},
        Metric.DAYS_OF_USE: {Statistic.MEAN},
        Metric.USER_COUNT: {Statistic.COUNT, Statistic.PERCENT},
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

    bypass_jetstream_check = True
    if outcomes_metadata is not None:
        bypass_jetstream_check = False
        metrics_set_from_jetstream = set(
            chain.from_iterable(
                [
                    outcomes_metadata[slug]["metrics"]
                    + outcomes_metadata[slug]["default_metrics"]
                    for slug in outcomes_metadata
                ]
            )
        )

    for metric in primary_outcome_metrics:
        # validate against jetstream metadata unless we couldn't get it
        if bypass_jetstream_check or metric.slug in metrics_set_from_jetstream:
            RESULTS_METRICS_MAP[metric.slug] = ALL_STATISTICS

            primary_metrics_set.add(metric.slug)

    for outcome_slug in secondary_outcome_slugs:
        RESULTS_METRICS_MAP[outcome_slug] = ALL_STATISTICS

    other_metrics_map, other_metrics = get_other_metrics_names_and_map(
        data, RESULTS_METRICS_MAP
    )
    RESULTS_METRICS_MAP |= other_metrics_map

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
    other_metrics_map = {k: {v} for k, v in other_metrics_map.items()}

    return other_metrics_map, other_metrics_names


def get_experiment_data(experiment):
    recipe_slug = experiment.slug.replace("-", "_")
    windows = [AnalysisWindow.DAILY, AnalysisWindow.WEEKLY, AnalysisWindow.OVERALL]
    raw_data = {
        AnalysisWindow.DAILY: {},
        AnalysisWindow.WEEKLY: {},
        AnalysisWindow.OVERALL: {},
    }

    experiment_metadata = get_metadata(recipe_slug)
    outcomes_metadata = (
        experiment_metadata.get("outcomes") if experiment_metadata is not None else None
    )

    experiment_errors = get_analysis_errors(recipe_slug)

    experiment_data_old = {
        "show_analysis": settings.FEATURE_ANALYSIS,
        "metadata": experiment_metadata,
    }
    experiment_data = {
        "show_analysis": settings.FEATURE_ANALYSIS,
        "metadata": experiment_metadata,
    }

    for window in windows:
        experiment_data[window] = {}
        experiment_data_old[window] = {}
        data_from_jetstream = get_data(recipe_slug, window) or []

        segment_points_enrollments = defaultdict(list)
        segment_points_exposures = defaultdict(list)

        for point in data_from_jetstream:
            if point["analysis_basis"] == AnalysisBasis.ENROLLMENTS:
                segment_points_enrollments[point["segment"]].append(point)
                experiment_data[window][AnalysisBasis.ENROLLMENTS] = {}
                raw_data[window][AnalysisBasis.ENROLLMENTS] = {}
            elif point["analysis_basis"] == AnalysisBasis.EXPOSURES:
                segment_points_exposures[point["segment"]].append(point)
                experiment_data[window][AnalysisBasis.EXPOSURES] = {}
                raw_data[window][AnalysisBasis.EXPOSURES] = {}

        for segment, segment_data in segment_points_enrollments.items():
            data = raw_data[window][AnalysisBasis.ENROLLMENTS][segment] = JetstreamData(
                __root__=(segment_data)
            )
            (
                result_metrics,
                primary_metrics_set,
                other_metrics,
            ) = get_results_metrics_map(
                data,
                experiment.primary_outcomes,
                experiment.secondary_outcomes,
                outcomes_metadata,
            )
            if data and window == AnalysisWindow.OVERALL:
                # Append some values onto Jetstream data
                data.append_population_percentages()
                data.append_retention_data(
                    raw_data[AnalysisWindow.WEEKLY][AnalysisBasis.ENROLLMENTS][segment]
                )

                ResultsObjectModel = create_results_object_model(data)
                data = ResultsObjectModel(result_metrics, data, experiment)
                data.append_conversion_count(primary_metrics_set)

                if segment == Segment.ALL:
                    experiment_data_old["other_metrics"] = other_metrics
                    experiment_data["other_metrics"] = other_metrics
            elif data and window == AnalysisWindow.WEEKLY:
                ResultsObjectModel = create_results_object_model(data)
                data = ResultsObjectModel(result_metrics, data, experiment, window)

            transformed_data = data.dict(exclude_none=True) or None
            experiment_data_old[window][segment] = transformed_data
            experiment_data[window][AnalysisBasis.ENROLLMENTS][segment] = transformed_data

        for segment, segment_data in segment_points_exposures.items():
            data = raw_data[window][AnalysisBasis.EXPOSURES][segment] = JetstreamData(
                __root__=(segment_data)
            )
            (
                result_metrics,
                primary_metrics_set,
                other_metrics,
            ) = get_results_metrics_map(
                data,
                experiment.primary_outcomes,
                experiment.secondary_outcomes,
                outcomes_metadata,
            )
            if data and window == AnalysisWindow.OVERALL:
                # Append some values onto Jetstream data
                data.append_population_percentages()
                data.append_retention_data(
                    raw_data[AnalysisWindow.WEEKLY][AnalysisBasis.EXPOSURES][segment]
                )

                ResultsObjectModel = create_results_object_model(data)
                data = ResultsObjectModel(result_metrics, data, experiment)
                data.append_conversion_count(primary_metrics_set)

            elif data and window == AnalysisWindow.WEEKLY:
                ResultsObjectModel = create_results_object_model(data)
                data = ResultsObjectModel(result_metrics, data, experiment, window)

            transformed_data = data.dict(exclude_none=True) or None
            experiment_data[window][AnalysisBasis.EXPOSURES][segment] = transformed_data

    errors_by_metric = {}
    errors_experiment_overall = []
    if experiment_errors is not None:
        for err in experiment_errors:
            metric_slug = err.get("metric")
            if "metric" in err and metric_slug is not None:
                if metric_slug not in errors_by_metric:
                    errors_by_metric[metric_slug] = []
                errors_by_metric[metric_slug].append(err)
            else:
                errors_experiment_overall.append(err)

    errors_by_metric["experiment"] = errors_experiment_overall

    experiment_data_old["errors"] = errors_by_metric
    experiment_data["errors"] = errors_by_metric

    return {"v1": experiment_data_old, "v2": experiment_data}
