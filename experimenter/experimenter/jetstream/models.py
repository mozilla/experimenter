from enum import StrEnum
from typing import Any

from mozilla_nimbus_schemas.jetstream import AnalysisBasis
from mozilla_nimbus_schemas.jetstream import Statistic as JetstreamStatisticResult
from pydantic import BaseModel, Field, RootModel, create_model, field_validator

from experimenter.experiments.models import NimbusExperiment


class AnalysisWindow(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    OVERALL = "overall"


class Significance(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class BranchComparison(StrEnum):
    ABSOLUTE = "absolute"
    DIFFERENCE = "difference"
    UPLIFT = "relative_uplift"


class Metric(StrEnum):
    RETENTION = "retained"
    RETENTION_3_DAYS = "active_in_last_3_days_legacy"
    SEARCH = "search_count"
    DAYS_OF_USE = "days_of_use"
    USER_COUNT = "identity"
    DAILY_ACTIVE_USERS = "client_level_daily_active_users_v2"


class Statistic(StrEnum):
    """
    This is the list of statistics supported in Experimenter,
    not a complete list of statistics available in Jetstream.
    """

    PERCENT = "percentage"
    BINOMIAL = "binomial"
    MEAN = "mean"
    COUNT = "count"
    POPULATION_RATIO = "population_ratio"
    PER_CLIENT_DAU_IMPACT = "per_client_dau_impact"
    LINEAR_MODEL_MEAN = "mean_lm"


class Segment(StrEnum):
    ALL = "all"


# TODO: Consider a "guardrail_metrics" group containing "days_of_use",
# "retained", and "search_count".
class Group(StrEnum):
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
    """Same as mozilla-nimbus-schemas `Statistic` but sets a default analysis_basis."""

    analysis_basis: AnalysisBasis = AnalysisBasis.ENROLLMENTS

    class Config:
        use_enum_values = True


class JetstreamData(RootModel[JetstreamDataPoint]):
    """
    Parameters:
        root: list[JetstreamDataPoint]
            The list should be filtered as needed coming in (e.g., by a given segment).
    """

    root: list[JetstreamDataPoint] = Field(default_factory=list)

    def __iter__(self):
        return iter(self.root)

    def __len__(self):
        return len(self.root)

    def append(self, item):
        self.root.append(item)

    def extend(self, item):
        self.root.extend(item)

    def get_segment(self):
        return self.root[0].segment or Segment.ALL

    def append_population_percentages(self):
        total_population = 0  # total enrolled population
        branches = {}

        for jetstream_data_point in self:
            if jetstream_data_point.metric == Metric.USER_COUNT:
                branches[jetstream_data_point.branch] = jetstream_data_point.point

        total_population = sum([b for b in branches.values() if b is not None])

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

    def get_retention_by_window(self, window_index, data, metric):
        data = data or []
        return [
            jetstream_data_point
            for jetstream_data_point in data
            if jetstream_data_point.window_index == str(window_index)
            and jetstream_data_point.metric == metric
        ]

    def append_retention_data(self, weekly_data):
        # Try to get the two-week retention data. If it doesn't
        # exist (experiment was too short), settle for 1 week.
        retention_data = self.get_retention_by_window(2, weekly_data, Metric.RETENTION)
        if len(retention_data) == 0:
            retention_data = self.get_retention_by_window(
                1, weekly_data, Metric.RETENTION
            )

        self.extend(retention_data)

    def append_retention_3_days(self, daily_data):
        # Extract the 3-day retention data (window index 4)
        # without falling back to earlier windows
        retention_data = self.get_retention_by_window(
            4, daily_data, Metric.RETENTION_3_DAYS
        )

        self.extend(retention_data)


class DataPoint(BaseModel):
    lower: float | None = None
    upper: float | None = None
    point: float | None = None
    window_index: str | None = None
    count: float | None = None

    @field_validator("window_index", mode="before")
    @classmethod
    def coerce_window_index(cls, v: Any):
        if isinstance(v, int):
            return str(v)

        return v

    def has_bounds(self) -> bool:
        return self.lower and self.upper


class BranchComparisonData(BaseModel):
    all: list[DataPoint] = Field(default_factory=list)
    first: DataPoint = Field(default_factory=DataPoint)


class SignificanceData(BaseModel):
    overall: dict[str, Any] = Field(default_factory=dict)
    weekly: dict[str, Any] = Field(default_factory=dict)
    daily: dict[str, Any] = Field(default_factory=dict)


class MetricData(BaseModel):
    absolute: BranchComparisonData = Field(default_factory=BranchComparisonData)
    difference: BranchComparisonData = Field(default_factory=BranchComparisonData)
    relative_uplift: BranchComparisonData = Field(default_factory=BranchComparisonData)
    significance: SignificanceData = Field(default_factory=BranchComparisonData)
    percent: float = None


def compute_significance(data_point: DataPoint) -> Significance:
    if max(data_point.lower, data_point.upper, 0) == 0:
        return Significance.NEGATIVE

    if min(data_point.lower, data_point.upper, 0) == 0:
        return Significance.POSITIVE

    return Significance.NEUTRAL


class ResultsObjectModelBase(BaseModel):
    def __init__(
        self,
        result_metrics: dict[str, set[Statistic]],
        data: JetstreamData,
        experiment: NimbusExperiment,
        window: AnalysisWindow = AnalysisWindow.OVERALL,
    ):
        super().__init__()

        assert experiment.reference_branch

        for jetstream_data_point in data:
            metric = jetstream_data_point.metric
            statistic = jetstream_data_point.statistic

            if metric in result_metrics and statistic in result_metrics[metric]:
                # We added an improved LINEAR_MODEL_MEAN statistic that should supercede
                # MEAN when available, but we still want MEAN if it isn't available
                if (
                    statistic == Statistic.MEAN
                    and Statistic.LINEAR_MODEL_MEAN in result_metrics[metric]
                    and len(
                        [
                            d
                            for d in data
                            if d.metric == metric
                            and d.statistic == Statistic.LINEAR_MODEL_MEAN
                        ]
                    )
                    > 0
                ):
                    continue

                comparison_to_branch = jetstream_data_point.comparison_to_branch

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

                # Need window index for weekly DataPoint objects and for storing
                # significance for each window. Overall should always be 1 because
                # there is only ever one overall window.
                window_index = (
                    "1"
                    if window == AnalysisWindow.OVERALL
                    else jetstream_data_point.window_index
                )

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
                    significance = compute_significance(data_point)
                    if comparison_to_branch is not None:
                        significance_to_branch = getattr(
                            metric_data.significance, comparison_to_branch
                        )
                        getattr(significance_to_branch, window)[window_index] = (
                            significance
                        )

                if window == AnalysisWindow.WEEKLY:
                    data_point.window_index = window_index

                comparison_data = getattr(metric_data, branch_comparison)
                if branch_comparison == BranchComparison.ABSOLUTE:
                    if len(comparison_data.all) == 0:
                        comparison_data.first = data_point

                    comparison_data.all.append(data_point)

                # this is effectively an `else`, but we'll check just in case
                if comparison_to_branch is not None:
                    pairwise_comparison_data = getattr(
                        comparison_data, comparison_to_branch
                    )
                    if len(pairwise_comparison_data.all) == 0:
                        pairwise_comparison_data.first = data_point

                    pairwise_comparison_data.all.append(data_point)

    def append_conversion_count(self, primary_metrics_set):
        for branch_name in self.model_fields:
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


"""
    Dynamically create BranchData and ResultsObjectModel objects.
    These need to be dynamically created because their keys are
    variable.
"""


def create_results_object_model(data: JetstreamData):
    branches = {data_point.branch for data_point in data}

    # create a dynamic model with all branches, leveraging BranchComparisonData
    PairwiseBranchComparisonData = create_model(
        "PairwiseBranchComparisonData",
        **{
            branch: (BranchComparisonData, Field(default_factory=BranchComparisonData))
            for branch in branches
        },
    )

    # create a dynamic model with all branches, leveraging SignificanceData
    PairwiseSignificanceData = create_model(
        "PairwiseSignificanceData",
        **{
            branch: (SignificanceData, Field(default_factory=SignificanceData))
            for branch in branches
        },
    )

    class PairwiseMetricData(MetricData):
        difference: PairwiseBranchComparisonData = Field(
            default_factory=PairwiseBranchComparisonData
        )
        relative_uplift: PairwiseBranchComparisonData = Field(
            default_factory=PairwiseBranchComparisonData
        )
        significance: PairwiseSignificanceData = Field(
            default_factory=PairwiseSignificanceData
        )

    metrics = {data_point.metric for data_point in data}

    # Dynamically create our grouped models which are dependent on metrics
    # available for a given experiment
    SearchData = create_model(
        "SearchData",
        **{
            metric_name: (PairwiseMetricData, Field(default_factory=PairwiseMetricData))
            for metric_name in metrics
            if metric_name in SEARCH_METRICS
        },
    )

    UsageData = create_model(
        "UsageData",
        **{
            metric_name: (PairwiseMetricData, Field(default_factory=PairwiseMetricData))
            for metric_name in metrics
            if metric_name in USAGE_METRICS
        },
    )

    OtherData = create_model(
        "OtherData",
        **{
            metric_name: (PairwiseMetricData, Field(default_factory=PairwiseMetricData))
            for metric_name in metrics
            if metric_name not in SEARCH_METRICS + USAGE_METRICS
        },
    )

    class BranchData(BaseModel):
        search_metrics: SearchData = Field(default_factory=SearchData)
        usage_metrics: UsageData = Field(default_factory=UsageData)
        other_metrics: OtherData = Field(default_factory=OtherData)

    class Branch(BaseModel):
        is_control: bool = False
        branch_data: BranchData = Field(default_factory=BranchData)

    # Create ResultsObjectModel model which is dependent on
    # branches available for a given experiment
    return create_model(
        "ResultsObjectModel",
        **{branch: (Branch, Field(default_factory=Branch)) for branch in branches},
        __base__=ResultsObjectModelBase,
    )
