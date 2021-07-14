from django.conf import settings

from experimenter.jetstream.models import (
    BranchComparisonData,
    DataPoint,
    Group,
    JetstreamDataPoint,
    MetricData,
    SignificanceData,
)
from experimenter.jetstream.tests.constants import TestConstants


class JetstreamDataFactory:
    def get_metric_data(self, data_point):
        return MetricData(
            absolute=BranchComparisonData(first=data_point, all=[data_point]),
            difference=BranchComparisonData(),
            relative_uplift=BranchComparisonData(),
            significance=SignificanceData(),
        ).dict(exclude_none=True)

    def add_outcome_data(self, primary_outcome, data, weekly_data, overall_data):
        range_data = DataPoint(lower=2, point=4, upper=8)
        primary_metric = f"{primary_outcome}_ever_used"

        for branch in ["control", "variant"]:
            if Group.OTHER not in overall_data[branch]["branch_data"]:
                overall_data[branch]["branch_data"][Group.OTHER] = {}
            if Group.OTHER not in weekly_data[branch]["branch_data"]:
                weekly_data[branch]["branch_data"][Group.OTHER] = {}

            data_point_overall = range_data.copy()
            data_point_overall.count = 48.0
            overall_data[branch]["branch_data"][Group.OTHER][
                primary_metric
            ] = self.get_metric_data(data_point_overall)

            data_point_weekly = range_data.copy()
            data_point_weekly.window_index = "1"
            weekly_data[branch]["branch_data"][Group.OTHER][
                primary_metric
            ] = self.get_metric_data(data_point_weekly)

            data.append(
                JetstreamDataPoint(
                    **range_data.dict(exclude_none=True),
                    metric=primary_metric,
                    branch=branch,
                    statistic="binomial",
                    window_index="1",
                ).dict(exclude_none=True)
            )

    def generate_results_data(self, primary_outcomes):
        (
            DAILY_DATA,
            WEEKLY_DATA,
            OVERALL_DATA,
        ) = TestConstants.get_test_data()

        FULL_DATA = {
            "daily": DAILY_DATA,
            "weekly": WEEKLY_DATA,
            "overall": OVERALL_DATA,
            "other_metrics": {
                Group.OTHER: {
                    "some_count": "Some Count",
                    "another_count": "Another Count",
                },
            },
            "metadata": {"metrics": {}},
            "show_analysis": settings.FEATURE_ANALYSIS,
        }

        for primary_outcome in primary_outcomes:
            self.add_outcome_data(primary_outcome, DAILY_DATA, WEEKLY_DATA, OVERALL_DATA)

        return FULL_DATA
