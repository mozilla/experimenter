from typing import List

from pydantic import BaseModel, create_model


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
    PERCENT = "percentage"
    BINOMIAL = "binomial"
    MEAN = "mean"
    COUNT = "count"


class Segment:
    ALL = "all"


class JetstreamDataPoint(BaseModel):
    lower: float = None
    upper: float = None
    point: float = None
    metric: str = None
    branch: str = None
    statistic: str = None
    window_index: str = None
    comparison: str = None
    segment: str = Segment.ALL


class JetstreamData(BaseModel):
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

    def append_population_percentages(self):
        total_population = 0
        branches = {}
        for jetstream_data_point in self.__root__:
            if jetstream_data_point.segment != Segment.ALL:
                continue

            if jetstream_data_point.metric == Metric.USER_COUNT:
                total_population += jetstream_data_point.point
                branches[jetstream_data_point.branch] = jetstream_data_point.point

        for branch_name, branch_user_count in sorted(branches.items()):
            self.append(
                JetstreamDataPoint(
                    metric=Metric.USER_COUNT,
                    statistic=Statistic.PERCENT,
                    branch=branch_name,
                    point=round(branch_user_count / total_population * 100),
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
    overall: dict = {}
    weekly: dict = {}


class MetricData(BaseModel):
    absolute: BranchComparisonData
    difference: BranchComparisonData
    relative_uplift: BranchComparisonData
    significance: SignificanceData
    percent: float = None


class ResultsObjectModelBase(BaseModel):
    def __init__(self, result_metrics, data, experiment, window="overall"):
        super(ResultsObjectModelBase, self).__init__()

        for jetstream_data_point in data:
            if jetstream_data_point.segment != Segment.ALL:
                continue

            branch = jetstream_data_point.branch
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

            # For "overall" data, set window_index to 1 for uniformity
            window_index = 1 if window == "overall" else jetstream_data_point.window_index

            if metric in result_metrics and statistic in result_metrics[metric]:
                branch_obj = getattr(self, branch)
                branch_obj.is_control = experiment.reference_branch.slug == branch

                if metric == Metric.USER_COUNT and statistic == Statistic.PERCENT:
                    user_count_data = getattr(branch_obj.branch_data, Metric.USER_COUNT)
                    user_count_data.percent = data_point.point
                    continue

                metric_data = getattr(branch_obj.branch_data, metric)
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
        for branch_name in self.dict().keys():
            branch = getattr(self, branch_name)
            branch_data = branch.branch_data
            for primary_metric in primary_metrics_set:
                user_count_data = getattr(branch_data, Metric.USER_COUNT)
                absolute_user_counts = getattr(user_count_data, BranchComparison.ABSOLUTE)
                primary_metric_data = getattr(branch_data, primary_metric)
                absolute_primary_metric_vals = getattr(
                    primary_metric_data, BranchComparison.ABSOLUTE
                )

                population_count = absolute_user_counts.first.point
                conversion_percent = absolute_primary_metric_vals.first.point
                conversion_count = population_count * conversion_percent

                absolute_primary_metric_vals.first.count = conversion_count
                absolute_primary_metric_vals.all[0].count = conversion_count

    def compute_significance(self, data_point):
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


def create_results_object_model(data):
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

    # Create BranchData model which is dependent on metrics
    # available for a given experiment
    BranchData = create_model("BranchData", **metrics)

    class Branch(BaseModel):
        is_control: bool = False
        branch_data: BranchData

    for branch in branches:
        branches[branch] = Branch(is_control=False, branch_data=BranchData())

    # Create ResultsObjectModel model which is dependent on
    # branches available for a given experiment
    return create_model("ResultsObjectModel", **branches, __base__=ResultsObjectModelBase)
