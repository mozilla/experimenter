from typing import Any, Dict, List

from mozilla_nimbus_schemas.jetstream import AnalysisBasis
from mozilla_nimbus_schemas.jetstream import Statistic as JetstreamStatisticResult
from pydantic import BaseModel, create_model

from experimenter.experiments.models import NimbusExperiment


class AnalysisWindow:
    DAILY = "daily"
    WEEKLY = "weekly"
    OVERALL = "overall"


class Significance:
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class BranchComparison:
    ABSOLUTE = "absolute"
    DIFFERENCE = "difference"
    UPLIFT = "relative_uplift"


class Metric:
    RETENTION = "retained"
    SEARCH = "search_count"
    DAYS_OF_USE = "days_of_use"
    USER_COUNT = "identity"


class Statistic:
    """
    This is the list of statistics supported in Experimenter,
    not a complete list of statistics available in Jetstream.
    """

    PERCENT = "percentage"
    BINOMIAL = "binomial"
    MEAN = "mean"
    COUNT = "count"


class Segment:
    ALL = "all"


# TODO: Consider a "guardrail_metrics" group containing "days_of_use",
# "retained", and "search_count".
class Group:
    SEARCH = "search_metrics"
    USAGE = "usage_metrics"
    OTHER = "other_metrics"


SEARCH_METRICS = [
    "searches_with_ads",
    "search_count",
    "organic_search_count",
    "tagged_follow_on_search_count",
    "tagged_search_count",
]
USAGE_METRICS = [
    "uri_count",
    "active_hours",
]
GROUPED_METRICS = {
    Group.SEARCH: SEARCH_METRICS,
    Group.USAGE: USAGE_METRICS,
}


# A map of metric -> group for quick lookups.
METRIC_GROUP = {}
for group, metrics in GROUPED_METRICS.items():
    for metric in metrics:
        METRIC_GROUP[metric] = group


class JetstreamDataPoint(JetstreamStatisticResult):
    """
    Same as the mozilla-nimbus-schemas `Statistic` but sets a default analysis_basis.
    """

    analysis_basis: AnalysisBasis = AnalysisBasis.ENROLLMENTS


class JetstreamData(BaseModel):
    """
    Parameters:
        __root__: List[JetstreamDataPoint] = []
            The list should be filtered as needed coming in (e.g., by a given segment).
    """

    __root__: List[JetstreamDataPoint] = []

    def __iter__(self):
        return iter(self.__root__)

    def __len__(self):
        return len(self.__root__)

    def append(self, item):
        self.__root__.append(item)

    def extend(self, item):
        self.__root__.extend(item)

    def dict(self, exclude_none):
        return [item.dict(exclude_none=exclude_none) for item in self.__root__]

    def get_segment(self):
        return self.__root__[0].segment or Segment.ALL

    def append_population_percentages(self):
        total_population = 0
        branches = {}

        for jetstream_data_point in self.__root__:
            if jetstream_data_point.metric == Metric.USER_COUNT:
                if jetstream_data_point.point is not None:
                    total_population += jetstream_data_point.point
                branches[jetstream_data_point.branch] = jetstream_data_point.point

        for branch_name, branch_user_count in sorted(branches.items()):
            point = 0
            if total_population > 0:
                point = round(branch_user_count / total_population * 100)

            self.append(
                JetstreamDataPoint(
                    metric=Metric.USER_COUNT,
                    statistic=Statistic.PERCENT,
                    branch=branch_name,
                    point=point,
                    segment=self.get_segment(),
                )
            )

    def get_week_x_retention(self, week_index, weekly_data):
        weekly_data = weekly_data or []
        return [
            jetstream_data_point
            for jetstream_data_point in weekly_data
            if jetstream_data_point.window_index == str(week_index)
            and jetstream_data_point.metric == Metric.RETENTION
        ]

    def append_retention_data(self, weekly_data):
        # Try to get the two-week retention data. If it doesn't
        # exist (experiment was too short), settle for 1 week.
        retention_data = self.get_week_x_retention(2, weekly_data)
        if len(retention_data) == 0:
            retention_data = self.get_week_x_retention(1, weekly_data)

        self.extend(retention_data)


class DataPoint(BaseModel):
    lower: float = None
    upper: float = None
    point: float = None
    window_index: str = None
    count: float = None

    def set_window_index(self, window_index):
        self.window_index = window_index

    def has_bounds(self):
        return self.lower and self.upper


class BranchComparisonData(BaseModel):
    all: List[DataPoint] = []
    first: DataPoint = DataPoint()


class SignificanceData(BaseModel):
    overall: Dict[str, Any] = {}
    weekly: Dict[str, Any] = {}


class MetricData(BaseModel):
    absolute: BranchComparisonData
    difference: BranchComparisonData
    relative_uplift: BranchComparisonData
    significance: SignificanceData
    percent: float = None


class ResultsObjectModelBase(BaseModel):
    def __init__(
        self,
        result_metrics: dict[str, set[Statistic]],
        data: JetstreamData,
        experiment: NimbusExperiment,
        window=AnalysisWindow.OVERALL,
    ):
        super().__init__()

        for jetstream_data_point in data:
            metric = jetstream_data_point.metric
            statistic = jetstream_data_point.statistic

            branch_comparison = (
                BranchComparison.ABSOLUTE
                if jetstream_data_point.comparison is None
                else jetstream_data_point.comparison
            )
            data_point = DataPoint(
                lower=jetstream_data_point.lower,
                upper=jetstream_data_point.upper,
                point=jetstream_data_point.point,
            )

            # For AnalysisWindow.OVERALL data, set window_index to 1 for uniformity
            window_index = (
                1
                if window == AnalysisWindow.OVERALL
                else jetstream_data_point.window_index
            )

            if metric in result_metrics and statistic in result_metrics[metric]:
                branch = jetstream_data_point.branch
                branch_obj = getattr(self, branch)
                branch_obj.is_control = experiment.reference_branch.slug == branch
                group_obj = getattr(
                    branch_obj.branch_data, METRIC_GROUP.get(metric, Group.OTHER)
                )

                if metric == Metric.USER_COUNT and statistic == Statistic.PERCENT:
                    user_count_data = getattr(group_obj, Metric.USER_COUNT)
                    user_count_data.percent = data_point.point
                    continue

                metric_data = getattr(group_obj, metric)

                if (
                    branch_comparison == BranchComparison.DIFFERENCE
                    and data_point.has_bounds()
                ):
                    getattr(metric_data.significance, window)[
                        window_index
                    ] = self.compute_significance(data_point)

                if window == "weekly":
                    data_point.set_window_index(window_index)

                comparison_data = getattr(metric_data, branch_comparison)
                if len(comparison_data.all) == 0:
                    comparison_data.first = data_point

                comparison_data.all.append(data_point)

    def append_conversion_count(self, primary_metrics_set):
        for branch_name in self.dict():
            branch = getattr(self, branch_name)
            branch_data = branch.branch_data
            for primary_metric in primary_metrics_set:
                user_count_data = getattr(
                    getattr(branch_data, Group.OTHER), Metric.USER_COUNT
                )
                absolute_user_counts = getattr(user_count_data, BranchComparison.ABSOLUTE)
                primary_metric_data = getattr(
                    getattr(branch_data, METRIC_GROUP.get(primary_metric, Group.OTHER)),
                    primary_metric,
                    None,
                )
                if primary_metric_data is None:
                    continue

                absolute_primary_metric_vals = getattr(
                    primary_metric_data, BranchComparison.ABSOLUTE
                )

                if not absolute_primary_metric_vals.all:
                    continue

                population_count = absolute_user_counts.first.point
                conversion_percent = absolute_primary_metric_vals.first.point

                conversion_count = 0.0
                if None not in (population_count, conversion_percent):
                    conversion_count = population_count * conversion_percent

                absolute_primary_metric_vals.first.count = conversion_count
                absolute_primary_metric_vals.all[0].count = conversion_count

    def compute_significance(self, data_point: DataPoint):
        if max(data_point.lower, data_point.upper, 0) == 0:
            return Significance.NEGATIVE
        if min(data_point.lower, data_point.upper, 0) == 0:
            return Significance.POSITIVE
        else:
            return Significance.NEUTRAL


"""
    Dynamically create BranchData and ResultsObjectModel objects.
    These need to be dynamically created because their keys are
    variable.
"""


def create_results_object_model(data: JetstreamData):
    branches = {}
    metrics = {}
    for jetstream_data_point in data:
        branches[jetstream_data_point.branch] = {}
        metrics[jetstream_data_point.metric] = MetricData(
            absolute=BranchComparisonData(),
            difference=BranchComparisonData(),
            relative_uplift=BranchComparisonData(),
            significance=SignificanceData(),
        )

    search_data = {k: v for k, v in metrics.items() if k in SEARCH_METRICS}
    usage_data = {k: v for k, v in metrics.items() if k in USAGE_METRICS}
    other_data = {
        k: v for k, v in metrics.items() if k not in SEARCH_METRICS + USAGE_METRICS
    }

    # Dynamically create our grouped models which are dependent on metrics
    # available for a given experiment
    SearchData = create_model("SearchData", **search_data)
    UsageData = create_model("UsageData", **usage_data)
    OtherData = create_model("OtherData", **other_data)

    class BranchData(BaseModel):
        search_metrics: SearchData
        usage_metrics: UsageData
        other_metrics: OtherData

    class Branch(BaseModel):
        is_control: bool = False
        branch_data: BranchData

    for branch in branches:
        branches[branch] = Branch(
            is_control=False,
            branch_data=BranchData(
                search_metrics=SearchData(),
                usage_metrics=UsageData(),
                other_metrics=OtherData(),
            ),
        )

    # Create ResultsObjectModel model which is dependent on
    # branches available for a given experiment
    return create_model("ResultsObjectModel", **branches, __base__=ResultsObjectModelBase)
