from experimenter.jetstream.models import (
    BranchComparison,
    BranchComparisonData,
    DataPoint,
    Group,
    JetstreamDataPoint,
    Metric,
    MetricData,
    Significance,
    SignificanceData,
    Statistic,
)


class JetstreamTestData:
    @classmethod
    def get_absolute_metric_data(cls, DATA_POINT):
        return MetricData(
            absolute=BranchComparisonData(first=DATA_POINT, all=[DATA_POINT]),
            difference=BranchComparisonData(),
            relative_uplift=BranchComparisonData(),
            significance=SignificanceData(),
        )

    @classmethod
    def get_difference_metric_data(cls, DATA_POINT, SIGNIFICANCE, is_retention=False):
        all_data_points = [DATA_POINT]
        if is_retention:
            all_data_points.append(DATA_POINT)

        return MetricData(
            absolute=BranchComparisonData(),
            difference=BranchComparisonData(first=DATA_POINT, all=all_data_points),
            relative_uplift=BranchComparisonData(),
            significance=SIGNIFICANCE,
        )

    @classmethod
    def get_identity_row(cls):
        return JetstreamDataPoint(
            point=12,
            upper=13,
            lower=10,
            metric=Metric.USER_COUNT,
            statistic=Statistic.COUNT,
            window_index="1",
        )

    @classmethod
    def get_significance_data_row(cls, VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW):
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW = (
            VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.copy()
        )
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.point = -2.0
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.upper = -1.0
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.lower = -5.0
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.metric = Metric.RETENTION
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.statistic = Statistic.BINOMIAL

        CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW = (
            VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.copy()
        )
        CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW.point = 12.0
        CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW.upper = 13.0
        CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW.lower = -5.0
        CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW.branch = "control"

        return (
            VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW,
            CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW,
        )

    @classmethod
    def get_data_points(cls):
        DATA_POINT_A = DataPoint(lower=10, point=12, upper=13, window_index=1)
        DATA_POINT_F = DATA_POINT_A.copy()
        DATA_POINT_F.window_index = None

        DATA_POINT_B = DataPoint(lower=-5, point=12, upper=13, window_index=1)
        DATA_POINT_E = DATA_POINT_B.copy()
        DATA_POINT_E.window_index = None

        DATA_POINT_C = DataPoint(lower=-5, point=-2, upper=-1, window_index=1)
        DATA_POINT_D = DATA_POINT_C.copy()
        DATA_POINT_D.window_index = None

        ABSOLUTE_METRIC_DATA_A = cls.get_absolute_metric_data(DATA_POINT_A)
        ABSOLUTE_METRIC_DATA_F = cls.get_absolute_metric_data(DATA_POINT_F)
        ABSOLUTE_METRIC_DATA_F_WITH_PERCENT = ABSOLUTE_METRIC_DATA_F.copy()
        ABSOLUTE_METRIC_DATA_F_WITH_PERCENT.percent = 50.0
        return (
            DATA_POINT_A,
            DATA_POINT_F,
            DATA_POINT_B,
            DATA_POINT_E,
            DATA_POINT_C,
            DATA_POINT_D,
            ABSOLUTE_METRIC_DATA_A,
            ABSOLUTE_METRIC_DATA_F,
            ABSOLUTE_METRIC_DATA_F_WITH_PERCENT,
        )

    @classmethod
    def get_differences(
        cls,
        DATA_POINT_A,
        DATA_POINT_F,
        DATA_POINT_B,
        DATA_POINT_E,
        DATA_POINT_C,
        DATA_POINT_D,
    ):
        DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL = cls.get_difference_metric_data(
            DATA_POINT_B, SignificanceData(weekly={"1": Significance.NEUTRAL}, overall={})
        )
        DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE = cls.get_difference_metric_data(
            DATA_POINT_A,
            SignificanceData(weekly={"1": Significance.POSITIVE}, overall={}),
        )
        DIFFERENCE_METRIC_DATA_WEEKLY_NEGATIVE = cls.get_difference_metric_data(
            DATA_POINT_C,
            SignificanceData(weekly={"1": Significance.NEGATIVE}, overall={}),
        )
        DIFFERENCE_METRIC_DATA_OVERALL_NEUTRAL = cls.get_difference_metric_data(
            DATA_POINT_E,
            SignificanceData(weekly={}, overall={"1": Significance.NEUTRAL}),
            is_retention=True,
        )
        DIFFERENCE_METRIC_DATA_OVERALL_POSITIVE = cls.get_difference_metric_data(
            DATA_POINT_F,
            SignificanceData(weekly={}, overall={"1": Significance.POSITIVE}),
        )
        DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE = cls.get_difference_metric_data(
            DATA_POINT_D,
            SignificanceData(weekly={}, overall={"1": Significance.NEGATIVE}),
            is_retention=True,
        )

        return (
            DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL,
            DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE,
            DIFFERENCE_METRIC_DATA_WEEKLY_NEGATIVE,
            DIFFERENCE_METRIC_DATA_OVERALL_NEUTRAL,
            DIFFERENCE_METRIC_DATA_OVERALL_POSITIVE,
            DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE,
        )

    @classmethod
    def get_metric_data(cls, data_point):
        return MetricData(
            absolute=BranchComparisonData(first=data_point, all=[data_point]),
            difference=BranchComparisonData(),
            relative_uplift=BranchComparisonData(),
            significance=SignificanceData(),
        ).dict(exclude_none=True)

    @classmethod
    def add_outcome_data(cls, data, overall_data, weekly_data, primary_outcome):
        primary_metrics = ["default_browser_action"]
        range_data = DataPoint(lower=2, point=4, upper=8)

        for primary_metric in primary_metrics:
            for branch in ["control", "variant"]:
                if Group.OTHER not in overall_data[branch]["branch_data"]:
                    overall_data[branch]["branch_data"][Group.OTHER] = {}
                if Group.OTHER not in weekly_data[branch]["branch_data"]:
                    weekly_data[branch]["branch_data"][Group.OTHER] = {}

                data_point_overall = range_data.copy()
                data_point_overall.count = 48.0
                overall_data[branch]["branch_data"][Group.OTHER][
                    primary_metric
                ] = cls.get_metric_data(data_point_overall)

                data_point_weekly = range_data.copy()
                data_point_weekly.window_index = "1"
                weekly_data[branch]["branch_data"][Group.OTHER][
                    primary_metric
                ] = cls.get_metric_data(data_point_weekly)

                data.append(
                    JetstreamDataPoint(
                        **range_data.dict(exclude_none=True),
                        metric=primary_metric,
                        branch=branch,
                        statistic="binomial",
                        window_index="1",
                    ).dict(exclude_none=True)
                )

    @classmethod
    def add_all_outcome_data(
        cls,
        data,
        overall_data,
        weekly_data,
        primary_outcomes,
    ):
        for primary_outcome in primary_outcomes:
            cls.add_outcome_data(data, overall_data, weekly_data, primary_outcome)

    @classmethod
    def get_test_data(cls, primary_outcomes):
        DATA_IDENTITY_ROW = cls.get_identity_row()

        CONTROL_DATA_ROW = DATA_IDENTITY_ROW.copy()
        CONTROL_DATA_ROW.branch = "control"

        VARIANT_DATA_ROW = DATA_IDENTITY_ROW.copy()
        VARIANT_DATA_ROW.branch = "variant"

        SEGMENTED_ROW = VARIANT_DATA_ROW.copy()
        SEGMENTED_ROW.segment = "some_segment"

        VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN = DATA_IDENTITY_ROW.copy()
        VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.metric = "some_count"
        VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.statistic = Statistic.MEAN
        VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.branch = "variant"

        VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL = DATA_IDENTITY_ROW.copy()
        VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.metric = "another_count"
        VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.statistic = Statistic.BINOMIAL
        VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.branch = "variant"

        VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW = DATA_IDENTITY_ROW.copy()
        VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.comparison = BranchComparison.DIFFERENCE
        VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.metric = Metric.SEARCH
        VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.statistic = Statistic.MEAN
        VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.branch = "variant"

        (
            VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW,
            CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW,
        ) = cls.get_significance_data_row(VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW)

        DAILY_DATA = [
            CONTROL_DATA_ROW.dict(exclude_none=True),
            VARIANT_DATA_ROW.dict(exclude_none=True),
            SEGMENTED_ROW.dict(exclude_none=True),
            VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.dict(exclude_none=True),
            VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.dict(exclude_none=True),
            VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.dict(exclude_none=True),
            VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.dict(exclude_none=True),
            CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW.dict(exclude_none=True),
        ]

        (
            DATA_POINT_A,
            DATA_POINT_F,
            DATA_POINT_B,
            DATA_POINT_E,
            DATA_POINT_C,
            DATA_POINT_D,
            ABSOLUTE_METRIC_DATA_A,
            ABSOLUTE_METRIC_DATA_F,
            ABSOLUTE_METRIC_DATA_F_WITH_PERCENT,
        ) = cls.get_data_points()

        (
            DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL,
            DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE,
            DIFFERENCE_METRIC_DATA_WEEKLY_NEGATIVE,
            DIFFERENCE_METRIC_DATA_OVERALL_NEUTRAL,
            DIFFERENCE_METRIC_DATA_OVERALL_POSITIVE,
            DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE,
        ) = cls.get_differences(
            DATA_POINT_A,
            DATA_POINT_F,
            DATA_POINT_B,
            DATA_POINT_E,
            DATA_POINT_C,
            DATA_POINT_D,
        )

        EMPTY_METRIC_DATA = MetricData(
            absolute=BranchComparisonData(),
            difference=BranchComparisonData(),
            relative_uplift=BranchComparisonData(),
            significance=SignificanceData(),
        )

        WEEKLY_DATA = {
            "control": {
                "is_control": True,
                "branch_data": {
                    Group.SEARCH: {
                        "search_count": EMPTY_METRIC_DATA.dict(exclude_none=True),
                    },
                    Group.USAGE: {},
                    Group.OTHER: {
                        "identity": ABSOLUTE_METRIC_DATA_A.dict(exclude_none=True),
                        "some_count": EMPTY_METRIC_DATA.dict(exclude_none=True),
                        "another_count": EMPTY_METRIC_DATA.dict(exclude_none=True),
                        "retained": DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL.dict(
                            exclude_none=True
                        ),
                    },
                },
            },
            "variant": {
                "is_control": False,
                "branch_data": {
                    Group.SEARCH: {
                        "search_count": DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE.dict(
                            exclude_none=True
                        ),
                    },
                    Group.USAGE: {},
                    Group.OTHER: {
                        "identity": ABSOLUTE_METRIC_DATA_A.dict(exclude_none=True),
                        "some_count": ABSOLUTE_METRIC_DATA_A.dict(exclude_none=True),
                        "another_count": ABSOLUTE_METRIC_DATA_A.dict(exclude_none=True),
                        "retained": DIFFERENCE_METRIC_DATA_WEEKLY_NEGATIVE.dict(
                            exclude_none=True
                        ),
                    },
                },
            },
        }

        OVERALL_DATA = {
            "control": {
                "is_control": True,
                "branch_data": {
                    Group.SEARCH: {
                        "search_count": EMPTY_METRIC_DATA.dict(exclude_none=True),
                    },
                    Group.USAGE: {},
                    Group.OTHER: {
                        "identity": ABSOLUTE_METRIC_DATA_F_WITH_PERCENT.dict(
                            exclude_none=True
                        ),
                        "some_count": EMPTY_METRIC_DATA.dict(exclude_none=True),
                        "another_count": EMPTY_METRIC_DATA.dict(exclude_none=True),
                        "default_browser_action": EMPTY_METRIC_DATA.dict(
                            exclude_none=True
                        ),
                        "retained": DIFFERENCE_METRIC_DATA_OVERALL_NEUTRAL.dict(
                            exclude_none=True
                        ),
                    },
                },
            },
            "variant": {
                "is_control": False,
                "branch_data": {
                    Group.SEARCH: {
                        "search_count": DIFFERENCE_METRIC_DATA_OVERALL_POSITIVE.dict(
                            exclude_none=True
                        ),
                    },
                    Group.USAGE: {},
                    Group.OTHER: {
                        "identity": ABSOLUTE_METRIC_DATA_F_WITH_PERCENT.dict(
                            exclude_none=True
                        ),
                        "some_count": ABSOLUTE_METRIC_DATA_F.dict(exclude_none=True),
                        "another_count": ABSOLUTE_METRIC_DATA_F.dict(exclude_none=True),
                        "retained": DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE.dict(
                            exclude_none=True
                        ),
                    },
                },
            },
        }

        cls.add_all_outcome_data(
            DAILY_DATA,
            OVERALL_DATA,
            WEEKLY_DATA,
            primary_outcomes,
        )

        return (
            DAILY_DATA,
            WEEKLY_DATA,
            OVERALL_DATA,
        )


class ZeroJetstreamTestData(JetstreamTestData):
    @classmethod
    def get_identity_row(cls):
        return JetstreamDataPoint(
            point=0,
            upper=0,
            lower=0,
            metric=Metric.USER_COUNT,
            statistic=Statistic.COUNT,
            window_index="1",
        )

    @classmethod
    def get_significance_data_row(cls, VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW):
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW = (
            VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.copy()
        )
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.point = 0.0
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.upper = 0.0
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.lower = 0.0
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.metric = Metric.RETENTION
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.statistic = Statistic.BINOMIAL

        CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW = (
            VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.copy()
        )
        CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW.point = 0.0
        CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW.upper = 0.0
        CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW.lower = 0.0
        CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW.branch = "control"

        return (
            VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW,
            CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW,
        )

    @classmethod
    def get_data_points(cls):
        DATA_POINT_A = DataPoint(lower=0, point=0, upper=0, window_index=1)
        DATA_POINT_F = DATA_POINT_A.copy()
        DATA_POINT_F.window_index = None

        DATA_POINT_B = DataPoint(lower=0, point=0, upper=0, window_index=1)
        DATA_POINT_E = DATA_POINT_B.copy()
        DATA_POINT_E.window_index = None

        DATA_POINT_C = DataPoint(lower=0, point=0, upper=0, window_index=1)
        DATA_POINT_D = DATA_POINT_C.copy()
        DATA_POINT_D.window_index = None

        ABSOLUTE_METRIC_DATA_A = cls.get_absolute_metric_data(DATA_POINT_A)
        ABSOLUTE_METRIC_DATA_F = cls.get_absolute_metric_data(DATA_POINT_F)
        ABSOLUTE_METRIC_DATA_F_WITH_PERCENT = ABSOLUTE_METRIC_DATA_F.copy()
        ABSOLUTE_METRIC_DATA_F_WITH_PERCENT.percent = 0.0
        return (
            DATA_POINT_A,
            DATA_POINT_F,
            DATA_POINT_B,
            DATA_POINT_E,
            DATA_POINT_C,
            DATA_POINT_D,
            ABSOLUTE_METRIC_DATA_A,
            ABSOLUTE_METRIC_DATA_F,
            ABSOLUTE_METRIC_DATA_F_WITH_PERCENT,
        )

    @classmethod
    def get_differences(
        cls,
        DATA_POINT_A,
        DATA_POINT_F,
        DATA_POINT_B,
        DATA_POINT_E,
        DATA_POINT_C,
        DATA_POINT_D,
    ):
        DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL = cls.get_difference_metric_data(
            DATA_POINT_B, SignificanceData(weekly={}, overall={})
        )
        DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE = cls.get_difference_metric_data(
            DATA_POINT_A,
            SignificanceData(weekly={}, overall={}),
        )
        DIFFERENCE_METRIC_DATA_WEEKLY_NEGATIVE = cls.get_difference_metric_data(
            DATA_POINT_C,
            SignificanceData(weekly={}, overall={}),
        )
        DIFFERENCE_METRIC_DATA_OVERALL_NEUTRAL = cls.get_difference_metric_data(
            DATA_POINT_E,
            SignificanceData(weekly={}, overall={}),
            is_retention=True,
        )
        DIFFERENCE_METRIC_DATA_OVERALL_POSITIVE = cls.get_difference_metric_data(
            DATA_POINT_F,
            SignificanceData(weekly={}, overall={}),
        )
        DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE = cls.get_difference_metric_data(
            DATA_POINT_D,
            SignificanceData(weekly={}, overall={}),
            is_retention=True,
        )

        return (
            DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL,
            DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE,
            DIFFERENCE_METRIC_DATA_WEEKLY_NEGATIVE,
            DIFFERENCE_METRIC_DATA_OVERALL_NEUTRAL,
            DIFFERENCE_METRIC_DATA_OVERALL_POSITIVE,
            DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE,
        )

    @classmethod
    def add_outcome_data(cls, data, overall_data, weekly_data, primary_outcome):
        primary_metrics = ["default_browser_action"]
        range_data = DataPoint(lower=0, point=0, upper=0)

        for primary_metric in primary_metrics:
            for branch in ["control", "variant"]:
                if Group.OTHER not in overall_data[branch]["branch_data"]:
                    overall_data[branch]["branch_data"][Group.OTHER] = {}
                if Group.OTHER not in weekly_data[branch]["branch_data"]:
                    weekly_data[branch]["branch_data"][Group.OTHER] = {}

                data_point_overall = range_data.copy()
                data_point_overall.count = 0.0
                overall_data[branch]["branch_data"][Group.OTHER][
                    primary_metric
                ] = cls.get_metric_data(data_point_overall)

                data_point_weekly = range_data.copy()
                data_point_weekly.window_index = "1"
                weekly_data[branch]["branch_data"][Group.OTHER][
                    primary_metric
                ] = cls.get_metric_data(data_point_weekly)

                data.append(
                    JetstreamDataPoint(
                        **range_data.dict(exclude_none=True),
                        metric=primary_metric,
                        branch=branch,
                        statistic="binomial",
                        window_index="1",
                    ).dict(exclude_none=True)
                )


class NonePointJetstreamTestData(ZeroJetstreamTestData):
    @classmethod
    def get_identity_row(cls):
        return JetstreamDataPoint(
            point=None,
            upper=None,
            lower=None,
            metric=Metric.USER_COUNT,
            statistic=Statistic.COUNT,
            window_index=None,
        )

    @classmethod
    def get_data_points(cls):
        DATA_POINT_A = DataPoint(lower=None, point=None, upper=None, window_index=None)
        DATA_POINT_F = DATA_POINT_A.copy()
        DATA_POINT_F.window_index = None

        DATA_POINT_B = DataPoint(lower=None, point=None, upper=None, window_index=None)
        DATA_POINT_E = DATA_POINT_B.copy()
        DATA_POINT_E.window_index = None

        DATA_POINT_C = DataPoint(lower=None, point=None, upper=None, window_index=None)
        DATA_POINT_D = DATA_POINT_C.copy()
        DATA_POINT_D.window_index = None

        ABSOLUTE_METRIC_DATA_A = cls.get_absolute_metric_data(DATA_POINT_A)
        ABSOLUTE_METRIC_DATA_F = cls.get_absolute_metric_data(DATA_POINT_F)
        ABSOLUTE_METRIC_DATA_F_WITH_PERCENT = ABSOLUTE_METRIC_DATA_F.copy()
        ABSOLUTE_METRIC_DATA_F_WITH_PERCENT.percent = None
        return (
            DATA_POINT_A,
            DATA_POINT_F,
            DATA_POINT_B,
            DATA_POINT_E,
            DATA_POINT_C,
            DATA_POINT_D,
            ABSOLUTE_METRIC_DATA_A,
            ABSOLUTE_METRIC_DATA_F,
            ABSOLUTE_METRIC_DATA_F_WITH_PERCENT,
        )
