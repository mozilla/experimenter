from copy import deepcopy

from pydantic import create_model

from experimenter.jetstream.models import (
    AnalysisBasis,
    BranchComparison,
    BranchComparisonData,
    DataPoint,
    Group,
    JetstreamDataPoint,
    Metric,
    MetricData,
    Segment,
    Significance,
    SignificanceData,
    Statistic,
)

DEFAULT_TEST_BRANCHES = ["control", "variant"]


class JetstreamTestData:
    @classmethod
    def get_absolute_metric_data(cls, DATA_POINT):
        return MetricData(
            absolute=BranchComparisonData(first=DATA_POINT, all=[DATA_POINT]),
            difference=cls.get_pairwise_branch_comparison_data()(),
            relative_uplift=cls.get_pairwise_branch_comparison_data()(),
            significance=cls.get_pairwise_significance_data()(),
        )

    @classmethod
    def get_difference_metric_data(
        cls,
        DATA_POINT: DataPoint,
        SIGNIFICANCE: SignificanceData,
        is_retention=False,
        branches=DEFAULT_TEST_BRANCHES,
        comparison_to_branch="control",
    ):
        all_data_points = [DATA_POINT]
        if is_retention:
            all_data_points.append(DATA_POINT)

        # set up dicts of non-pairwise data
        # (populated if the comparison is to the reference control branch)
        significance = (
            deepcopy(SIGNIFICANCE.dict())
            if comparison_to_branch == "control"
            else SignificanceData().dict()
        )
        difference = (
            BranchComparisonData(first=DATA_POINT, all=all_data_points).dict()
            if comparison_to_branch == "control"
            else BranchComparisonData().dict()
        )

        # initialize pairwise branch comparisons inside dicts
        for branch in branches:
            significance[branch] = SignificanceData().dict()
            difference[branch] = BranchComparisonData().dict()

        # set the comparison branch's data
        significance[comparison_to_branch] = deepcopy(SIGNIFICANCE.dict())
        difference[comparison_to_branch] = BranchComparisonData(
            first=DATA_POINT, all=all_data_points
        ).dict()

        return MetricData(
            absolute=BranchComparisonData(),
            difference=cls.get_pairwise_branch_comparison_data()(**difference),
            relative_uplift=cls.get_pairwise_branch_comparison_data()(),
            significance=cls.get_pairwise_significance_data()(**significance),
        )

    @classmethod
    def get_pairwise_branch_comparison_data(cls, branches=None):
        if not branches:
            branches = DEFAULT_TEST_BRANCHES
        branches_data = {b: BranchComparisonData() for b in branches}
        return create_model(
            "PairwiseBranchComparisonData",
            **branches_data,
            __base__=BranchComparisonData,
        )

    @classmethod
    def get_pairwise_significance_data(cls, branches=None):
        if not branches:
            branches = DEFAULT_TEST_BRANCHES
        # create a dynamic model that extends SignificanceData with all branches
        branches_significance_data = {b: SignificanceData() for b in branches}
        return create_model(
            "PairwiseSignificanceData",
            **branches_significance_data,
            __base__=SignificanceData,
        )

    @classmethod
    def get_identity_row(cls):
        return JetstreamDataPoint(
            point=12,
            upper=13,
            lower=10,
            branch="control",
            metric=Metric.USER_COUNT,
            statistic=Statistic.COUNT,
            window_index="1",
            segment=Segment.ALL,
            analysis_basis=AnalysisBasis.ENROLLMENTS,
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
        CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW.comparison_to_branch = "variant"

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
        DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL_CONTROL = cls.get_difference_metric_data(
            DATA_POINT_B,
            SignificanceData(weekly={"1": Significance.NEUTRAL.value}, overall={}),
            comparison_to_branch="control",
        )
        DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE_CONTROL = cls.get_difference_metric_data(
            DATA_POINT_A,
            SignificanceData(weekly={"1": Significance.POSITIVE.value}, overall={}),
            comparison_to_branch="control",
        )
        DIFFERENCE_METRIC_DATA_WEEKLY_NEGATIVE_CONTROL = cls.get_difference_metric_data(
            DATA_POINT_C,
            SignificanceData(weekly={"1": Significance.NEGATIVE.value}, overall={}),
            comparison_to_branch="control",
        )
        DIFFERENCE_METRIC_DATA_OVERALL_NEUTRAL_CONTROL = cls.get_difference_metric_data(
            DATA_POINT_E,
            SignificanceData(weekly={}, overall={"1": Significance.NEUTRAL.value}),
            comparison_to_branch="control",
        )
        DIFFERENCE_METRIC_DATA_OVERALL_POSITIVE_CONTROL = cls.get_difference_metric_data(
            DATA_POINT_F,
            SignificanceData(weekly={}, overall={"1": Significance.POSITIVE.value}),
            comparison_to_branch="control",
        )
        DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE_CONTROL = cls.get_difference_metric_data(
            DATA_POINT_D,
            SignificanceData(weekly={}, overall={"1": Significance.NEGATIVE.value}),
            comparison_to_branch="control",
        )
        DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL_VARIANT = cls.get_difference_metric_data(
            DATA_POINT_B,
            SignificanceData(weekly={"1": Significance.NEUTRAL.value}, overall={}),
            comparison_to_branch="variant",
        )
        DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE_VARIANT = cls.get_difference_metric_data(
            DATA_POINT_A,
            SignificanceData(weekly={"1": Significance.POSITIVE.value}, overall={}),
            comparison_to_branch="variant",
        )
        DIFFERENCE_METRIC_DATA_WEEKLY_NEGATIVE_VARIANT = cls.get_difference_metric_data(
            DATA_POINT_C,
            SignificanceData(weekly={"1": Significance.NEGATIVE.value}, overall={}),
            comparison_to_branch="variant",
        )
        DIFFERENCE_METRIC_DATA_OVERALL_NEUTRAL_VARIANT = cls.get_difference_metric_data(
            DATA_POINT_E,
            SignificanceData(weekly={}, overall={"1": Significance.NEUTRAL.value}),
            comparison_to_branch="variant",
        )
        DIFFERENCE_METRIC_DATA_OVERALL_POSITIVE_VARIANT = cls.get_difference_metric_data(
            DATA_POINT_F,
            SignificanceData(weekly={}, overall={"1": Significance.POSITIVE.value}),
            comparison_to_branch="variant",
        )
        DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE_VARIANT = cls.get_difference_metric_data(
            DATA_POINT_D,
            SignificanceData(weekly={}, overall={"1": Significance.NEGATIVE.value}),
            comparison_to_branch="variant",
        )

        return (
            DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL_CONTROL,
            DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL_VARIANT,
            DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE_CONTROL,
            DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE_VARIANT,
            DIFFERENCE_METRIC_DATA_WEEKLY_NEGATIVE_CONTROL,
            DIFFERENCE_METRIC_DATA_WEEKLY_NEGATIVE_VARIANT,
            DIFFERENCE_METRIC_DATA_OVERALL_NEUTRAL_CONTROL,
            DIFFERENCE_METRIC_DATA_OVERALL_NEUTRAL_VARIANT,
            DIFFERENCE_METRIC_DATA_OVERALL_POSITIVE_CONTROL,
            DIFFERENCE_METRIC_DATA_OVERALL_POSITIVE_VARIANT,
            DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE_CONTROL,
            DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE_VARIANT,
        )

    @classmethod
    def get_metric_data(cls, data_point):
        return MetricData(
            absolute=BranchComparisonData(first=data_point, all=[data_point]),
            difference=cls.get_pairwise_branch_comparison_data()(),
            relative_uplift=cls.get_pairwise_branch_comparison_data()(),
            significance=cls.get_pairwise_significance_data()(),
        ).dict(exclude_none=True)

    @classmethod
    def add_outcome_data(
        cls, data, overall_data, weekly_data, primary_outcome, analysis_basis
    ):
        primary_metrics = ["default_browser_action"]
        range_data = DataPoint(lower=2, point=4, upper=8)

        for primary_metric in primary_metrics:
            for branch in DEFAULT_TEST_BRANCHES:
                if Group.OTHER not in overall_data[branch]["branch_data"]:
                    overall_data[branch]["branch_data"][Group.OTHER.value] = {}
                if Group.OTHER not in weekly_data[branch]["branch_data"]:
                    weekly_data[branch]["branch_data"][Group.OTHER.value] = {}

                data_point_overall = range_data.copy()
                data_point_overall.count = 48.0
                overall_data[branch]["branch_data"][Group.OTHER.value][
                    primary_metric
                ] = cls.get_metric_data(data_point_overall)

                data_point_weekly = range_data.copy()
                data_point_weekly.window_index = "1"
                weekly_data[branch]["branch_data"][Group.OTHER.value][
                    primary_metric
                ] = cls.get_metric_data(data_point_weekly)

                data.append(
                    JetstreamDataPoint(
                        **range_data.dict(exclude_none=True),
                        metric=primary_metric,
                        branch=branch,
                        statistic="binomial",
                        window_index="1",
                        segment=Segment.ALL,
                        analysis_basis=analysis_basis,
                    ).dict(exclude_none=True)
                )

    @classmethod
    def add_outcome_data_mean(
        cls, data, overall_data, weekly_data, primary_outcome, analysis_basis
    ):
        primary_metrics = ["mozilla_default_browser"]
        range_data = DataPoint(lower=0, point=0, upper=0)

        for primary_metric in primary_metrics:
            for branch in DEFAULT_TEST_BRANCHES:
                if Group.OTHER not in overall_data[branch]["branch_data"]:
                    overall_data[branch]["branch_data"][Group.OTHER.value] = {}
                if Group.OTHER not in weekly_data[branch]["branch_data"]:
                    weekly_data[branch]["branch_data"][Group.OTHER.value] = {}

                data_point_overall = range_data.copy()
                data_point_overall.count = 0.0
                overall_data[branch]["branch_data"][Group.OTHER.value][
                    primary_metric
                ] = cls.get_metric_data(data_point_overall)

                data_point_weekly = range_data.copy()
                data_point_weekly.window_index = "1"
                weekly_data[branch]["branch_data"][Group.OTHER.value][
                    primary_metric
                ] = cls.get_metric_data(data_point_weekly)

                data.append(
                    JetstreamDataPoint(
                        **range_data.dict(exclude_none=True),
                        metric=primary_metric,
                        branch=branch,
                        statistic="mean",
                        window_index="1",
                        segment=Segment.ALL,
                        analysis_basis=analysis_basis,
                    ).dict(exclude_none=True)
                )

    @classmethod
    def add_all_outcome_data(
        cls,
        data,
        overall_data,
        weekly_data,
        primary_outcomes,
        analysis_basis,
    ):
        for primary_outcome in primary_outcomes:
            cls.add_outcome_data(
                data, overall_data, weekly_data, primary_outcome, analysis_basis
            )
            cls.add_outcome_data_mean(
                data, overall_data, weekly_data, primary_outcome, analysis_basis
            )

    @classmethod
    def get_test_data(cls, primary_outcomes):
        DATA_IDENTITY_ROW = cls.get_identity_row()

        CONTROL_DATA_ROW = DATA_IDENTITY_ROW.copy()
        CONTROL_DATA_ROW.branch = "control"

        VARIANT_DATA_ROW = DATA_IDENTITY_ROW.copy()
        VARIANT_DATA_ROW.branch = "variant"

        SEGMENTED_ROW_VARIANT = VARIANT_DATA_ROW.copy()
        SEGMENTED_ROW_VARIANT.segment = "some_segment"
        SEGMENTED_ROW_CONTROL = CONTROL_DATA_ROW.copy()
        SEGMENTED_ROW_CONTROL.segment = "some_segment"

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
        VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.comparison_to_branch = "control"

        BROKEN_STATISTIC_DATA_ROW = CONTROL_DATA_ROW.copy()
        BROKEN_STATISTIC_DATA_ROW.comparison = BranchComparison.ABSOLUTE
        BROKEN_STATISTIC_DATA_ROW.metric = "custom_metric"
        BROKEN_STATISTIC_DATA_ROW.statistic = "something_else"

        VARIANT_BROKEN_STATISTIC_DATA_ROW = VARIANT_DATA_ROW.copy()
        VARIANT_BROKEN_STATISTIC_DATA_ROW.comparison = BranchComparison.ABSOLUTE
        VARIANT_BROKEN_STATISTIC_DATA_ROW.metric = "custom_metric"
        VARIANT_BROKEN_STATISTIC_DATA_ROW.statistic = "something_else"

        EXPOSURES_BROKEN_STATISTIC_DATA_ROW = BROKEN_STATISTIC_DATA_ROW.copy()
        EXPOSURES_BROKEN_STATISTIC_DATA_ROW.analysis_basis = AnalysisBasis.EXPOSURES

        VARIANT_EXPOSURES_BROKEN_STATISTIC_DATA_ROW = (
            VARIANT_BROKEN_STATISTIC_DATA_ROW.copy()
        )
        VARIANT_EXPOSURES_BROKEN_STATISTIC_DATA_ROW.analysis_basis = (
            AnalysisBasis.EXPOSURES
        )

        (
            VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW,
            CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW,
        ) = cls.get_significance_data_row(VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW)

        # exposures
        EXPOSURES_CONTROL_DATA_ROW = DATA_IDENTITY_ROW.copy()
        EXPOSURES_CONTROL_DATA_ROW.branch = "control"
        EXPOSURES_CONTROL_DATA_ROW.analysis_basis = AnalysisBasis.EXPOSURES

        EXPOSURES_VARIANT_DATA_ROW = DATA_IDENTITY_ROW.copy()
        EXPOSURES_VARIANT_DATA_ROW.branch = "variant"
        EXPOSURES_VARIANT_DATA_ROW.analysis_basis = AnalysisBasis.EXPOSURES

        EXPOSURES_SEGMENTED_ROW_VARIANT = VARIANT_DATA_ROW.copy()
        EXPOSURES_SEGMENTED_ROW_VARIANT.segment = "some_segment"
        EXPOSURES_SEGMENTED_ROW_VARIANT.analysis_basis = AnalysisBasis.EXPOSURES
        EXPOSURES_SEGMENTED_ROW_CONTROL = CONTROL_DATA_ROW.copy()
        EXPOSURES_SEGMENTED_ROW_CONTROL.segment = "some_segment"
        EXPOSURES_SEGMENTED_ROW_CONTROL.analysis_basis = AnalysisBasis.EXPOSURES

        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN = DATA_IDENTITY_ROW.copy()
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.metric = "some_count"
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.statistic = Statistic.MEAN
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.branch = "variant"
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.analysis_basis = (
            AnalysisBasis.EXPOSURES
        )

        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL = DATA_IDENTITY_ROW.copy()
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.metric = "another_count"
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.statistic = Statistic.BINOMIAL
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.branch = "variant"
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.analysis_basis = (
            AnalysisBasis.EXPOSURES
        )

        EXPOSURES_VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW = DATA_IDENTITY_ROW.copy()
        EXPOSURES_VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.comparison = (
            BranchComparison.DIFFERENCE
        )
        EXPOSURES_VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.metric = Metric.SEARCH
        EXPOSURES_VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.statistic = Statistic.MEAN
        EXPOSURES_VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.branch = "variant"
        EXPOSURES_VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.comparison_to_branch = "control"
        EXPOSURES_VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.analysis_basis = (
            AnalysisBasis.EXPOSURES
        )

        (
            EXPOSURES_VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW,
            EXPOSURES_CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW,
        ) = cls.get_significance_data_row(
            EXPOSURES_VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW
        )

        DAILY_DATA = [
            CONTROL_DATA_ROW.dict(exclude_none=True),
            VARIANT_DATA_ROW.dict(exclude_none=True),
            VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.dict(exclude_none=True),
            VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.dict(exclude_none=True),
            VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.dict(exclude_none=True),
            VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.dict(exclude_none=True),
            CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW.dict(exclude_none=True),
            BROKEN_STATISTIC_DATA_ROW.dict(exclude_none=True),
            VARIANT_BROKEN_STATISTIC_DATA_ROW.dict(exclude_none=True),
        ]
        DAILY_EXPOSURES_DATA = [
            EXPOSURES_CONTROL_DATA_ROW.dict(exclude_none=True),
            EXPOSURES_VARIANT_DATA_ROW.dict(exclude_none=True),
            EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.dict(exclude_none=True),
            EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.dict(exclude_none=True),
            EXPOSURES_VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.dict(exclude_none=True),
            EXPOSURES_VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.dict(exclude_none=True),
            EXPOSURES_CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW.dict(exclude_none=True),
            EXPOSURES_BROKEN_STATISTIC_DATA_ROW.dict(exclude_none=True),
            VARIANT_EXPOSURES_BROKEN_STATISTIC_DATA_ROW.dict(exclude_none=True),
        ]
        SEGMENT_DATA = [
            SEGMENTED_ROW_VARIANT.dict(exclude_none=True),
            SEGMENTED_ROW_CONTROL.dict(exclude_none=True),
        ]
        SEGMENT_EXPOSURES_DATA = [
            EXPOSURES_SEGMENTED_ROW_VARIANT.dict(exclude_none=True),
            EXPOSURES_SEGMENTED_ROW_CONTROL.dict(exclude_none=True),
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
            DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL_CONTROL,
            DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL_VARIANT,
            DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE_CONTROL,
            DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE_VARIANT,
            DIFFERENCE_METRIC_DATA_WEEKLY_NEGATIVE_CONTROL,
            DIFFERENCE_METRIC_DATA_WEEKLY_NEGATIVE_VARIANT,
            DIFFERENCE_METRIC_DATA_OVERALL_NEUTRAL_CONTROL,
            DIFFERENCE_METRIC_DATA_OVERALL_NEUTRAL_VARIANT,
            DIFFERENCE_METRIC_DATA_OVERALL_POSITIVE_CONTROL,
            DIFFERENCE_METRIC_DATA_OVERALL_POSITIVE_VARIANT,
            DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE_CONTROL,
            DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE_VARIANT,
        ) = cls.get_differences(
            DATA_POINT_A,
            DATA_POINT_F,
            DATA_POINT_B,
            DATA_POINT_E,
            DATA_POINT_C,
            DATA_POINT_D,
        )

        PairwiseBranchComparisonData = cls.get_pairwise_branch_comparison_data()
        PairwiseSignificanceData = cls.get_pairwise_significance_data()

        EMPTY_METRIC_DATA = MetricData(
            absolute=BranchComparisonData(),
            difference=PairwiseBranchComparisonData(),
            relative_uplift=PairwiseBranchComparisonData(),
            significance=PairwiseSignificanceData(),
        )

        WEEKLY_DATA = {
            "control": {
                "is_control": True,
                "branch_data": {
                    Group.SEARCH.value: {
                        "search_count": EMPTY_METRIC_DATA.dict(exclude_none=True),
                    },
                    Group.USAGE.value: {},
                    Group.OTHER.value: {
                        "identity": ABSOLUTE_METRIC_DATA_A.dict(exclude_none=True),
                        "some_count": EMPTY_METRIC_DATA.dict(exclude_none=True),
                        "another_count": EMPTY_METRIC_DATA.dict(exclude_none=True),
                        "retained": DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL_VARIANT.dict(
                            exclude_none=True
                        ),
                        "custom_metric": EMPTY_METRIC_DATA.dict(exclude_none=True),
                    },
                },
            },
            "variant": {
                "is_control": False,
                "branch_data": {
                    Group.SEARCH.value: {
                        "search_count": (
                            DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE_CONTROL.dict(
                                exclude_none=True
                            )
                        ),
                    },
                    Group.USAGE.value: {},
                    Group.OTHER.value: {
                        "identity": ABSOLUTE_METRIC_DATA_A.dict(exclude_none=True),
                        "some_count": ABSOLUTE_METRIC_DATA_A.dict(exclude_none=True),
                        "another_count": ABSOLUTE_METRIC_DATA_A.dict(exclude_none=True),
                        "retained": DIFFERENCE_METRIC_DATA_WEEKLY_NEGATIVE_CONTROL.dict(
                            exclude_none=True
                        ),
                        "custom_metric": EMPTY_METRIC_DATA.dict(exclude_none=True),
                    },
                },
            },
        }

        OVERALL_DATA = {
            "control": {
                "is_control": True,
                "branch_data": {
                    Group.SEARCH.value: {
                        "search_count": EMPTY_METRIC_DATA.dict(exclude_none=True),
                    },
                    Group.USAGE.value: {},
                    Group.OTHER.value: {
                        "identity": ABSOLUTE_METRIC_DATA_F_WITH_PERCENT.dict(
                            exclude_none=True
                        ),
                        "some_count": EMPTY_METRIC_DATA.dict(exclude_none=True),
                        "another_count": EMPTY_METRIC_DATA.dict(exclude_none=True),
                        "default_browser_action": EMPTY_METRIC_DATA.dict(
                            exclude_none=True
                        ),
                        "retained": DIFFERENCE_METRIC_DATA_OVERALL_NEUTRAL_VARIANT.dict(
                            exclude_none=True
                        ),
                        "custom_metric": EMPTY_METRIC_DATA.dict(exclude_none=True),
                    },
                },
            },
            "variant": {
                "is_control": False,
                "branch_data": {
                    Group.SEARCH.value: {
                        "search_count": (
                            DIFFERENCE_METRIC_DATA_OVERALL_POSITIVE_CONTROL.dict(
                                exclude_none=True
                            )
                        ),
                    },
                    Group.USAGE.value: {},
                    Group.OTHER.value: {
                        "identity": ABSOLUTE_METRIC_DATA_F_WITH_PERCENT.dict(
                            exclude_none=True
                        ),
                        "some_count": ABSOLUTE_METRIC_DATA_F.dict(exclude_none=True),
                        "another_count": ABSOLUTE_METRIC_DATA_F.dict(exclude_none=True),
                        "retained": DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE_CONTROL.dict(
                            exclude_none=True
                        ),
                        "custom_metric": EMPTY_METRIC_DATA.dict(exclude_none=True),
                    },
                },
            },
        }

        ERRORS = {
            "experiment": [
                {
                    "exception": "(<class 'NoEnrollmentPeriodException'>)",
                    "exception_type": "NoEnrollmentPeriodException",
                    "experiment": "test-experiment-slug",
                    "filename": "cli.py",
                    "func_name": "execute",
                    "log_level": "ERROR",
                    "message": "test-experiment-slug -> error",
                    "metric": None,
                    "statistic": None,
                    "timestamp": "2022-08-31T04:32:03+00:00",
                    "analysis_basis": "enrollments",
                    "segment": "all",
                },
                {
                    "exception": "(<class 'NoEnrollmentPeriodException'>)",
                    "exception_type": "NoEnrollmentPeriodException",
                    "experiment": "test-experiment-slug",
                    "filename": "cli.py",
                    "func_name": "execute",
                    "log_level": "ERROR",
                    "message": "test-experiment-slug -> error",
                    "metric": None,
                    "statistic": None,
                    "timestamp": "2022-08-31T04:32:04",
                    "analysis_basis": "enrollments",
                    "segment": "all",
                },
                {
                    "exception": "(<class 'NoEnrollmentPeriodException'>)",
                    "exception_type": "NoEnrollmentPeriodException",
                    "experiment": "test-experiment-slug",
                    "filename": "cli.py",
                    "func_name": "execute",
                    "log_level": "ERROR",
                    "message": "test-experiment-slug -> error",
                    "metric": None,
                    "statistic": None,
                    "timestamp": "2022-08-31T04:32:05",
                    "analysis_basis": "enrollments",
                    "segment": "all",
                },
            ],
            "default_browser_action": [
                {
                    "exception": "(<class 'StatisticComputationException'>)",
                    "exception_type": "StatisticComputationException",
                    "experiment": "test-experiment-slug",
                    "filename": "statistics.py",
                    "func_name": "apply",
                    "log_level": "ERROR",
                    "message": "Error while computing statistic bootstrap_mean",
                    "metric": "default_browser_action",
                    "statistic": "bootstrap_mean",
                    "timestamp": "2022-08-31T04:32:03+00:00",
                    "analysis_basis": "enrollments",
                    "segment": "all",
                }
            ],
            "spoc_tiles_disable_rate": [
                {
                    "exception": "(<class 'StatisticComputationException'>)",
                    "exception_type": "StatisticComputationException",
                    "experiment": "test-experiment-slug",
                    "filename": "statistics.py",
                    "func_name": "apply",
                    "log_level": "ERROR",
                    "message": "Error while computing statistic binomial",
                    "metric": "spoc_tiles_disable_rate",
                    "statistic": "binomial",
                    "timestamp": "2022-08-31T04:32:03+00:00",
                    "analysis_basis": "enrollments",
                    "segment": "all",
                }
            ],
        }

        cls.add_all_outcome_data(
            DAILY_DATA,
            OVERALL_DATA,
            WEEKLY_DATA,
            primary_outcomes,
            AnalysisBasis.ENROLLMENTS,
        )
        cls.add_all_outcome_data(
            DAILY_EXPOSURES_DATA,
            OVERALL_DATA,
            WEEKLY_DATA,
            primary_outcomes,
            AnalysisBasis.EXPOSURES,
        )

        return (
            DAILY_DATA,
            WEEKLY_DATA,
            OVERALL_DATA,
            ERRORS,
            SEGMENT_DATA,
            DAILY_EXPOSURES_DATA,
            SEGMENT_EXPOSURES_DATA,
        )

    @classmethod
    def get_partial_exposures_test_data(cls, primary_outcomes):
        # similar to above but missing weekly retention metric for exposures
        DATA_IDENTITY_ROW = cls.get_identity_row()

        CONTROL_DATA_ROW = DATA_IDENTITY_ROW.copy()
        CONTROL_DATA_ROW.branch = "control"

        VARIANT_DATA_ROW = DATA_IDENTITY_ROW.copy()
        VARIANT_DATA_ROW.branch = "variant"

        SEGMENTED_ROW_VARIANT = VARIANT_DATA_ROW.copy()
        SEGMENTED_ROW_VARIANT.segment = "some_segment"
        SEGMENTED_ROW_CONTROL = CONTROL_DATA_ROW.copy()
        SEGMENTED_ROW_CONTROL.segment = "some_segment"

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
        VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.comparison_to_branch = "control"

        (
            VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW,
            CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW,
        ) = cls.get_significance_data_row(VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW)

        # exposures
        EXPOSURES_CONTROL_DATA_ROW = DATA_IDENTITY_ROW.copy()
        EXPOSURES_CONTROL_DATA_ROW.branch = "control"
        EXPOSURES_CONTROL_DATA_ROW.analysis_basis = AnalysisBasis.EXPOSURES

        EXPOSURES_VARIANT_DATA_ROW = DATA_IDENTITY_ROW.copy()
        EXPOSURES_VARIANT_DATA_ROW.branch = "variant"
        EXPOSURES_VARIANT_DATA_ROW.analysis_basis = AnalysisBasis.EXPOSURES

        EXPOSURES_SEGMENTED_ROW_VARIANT = VARIANT_DATA_ROW.copy()
        EXPOSURES_SEGMENTED_ROW_VARIANT.segment = "some_segment"
        EXPOSURES_SEGMENTED_ROW_VARIANT.analysis_basis = AnalysisBasis.EXPOSURES
        EXPOSURES_SEGMENTED_ROW_CONTROL = CONTROL_DATA_ROW.copy()
        EXPOSURES_SEGMENTED_ROW_CONTROL.segment = "some_segment"
        EXPOSURES_SEGMENTED_ROW_CONTROL.analysis_basis = AnalysisBasis.EXPOSURES

        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN = DATA_IDENTITY_ROW.copy()
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.metric = "some_count"
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.statistic = Statistic.MEAN
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.branch = "variant"
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.analysis_basis = (
            AnalysisBasis.EXPOSURES
        )

        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL = DATA_IDENTITY_ROW.copy()
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.metric = "another_count"
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.statistic = Statistic.BINOMIAL
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.branch = "variant"
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.analysis_basis = (
            AnalysisBasis.EXPOSURES
        )

        DAILY_DATA = [
            CONTROL_DATA_ROW.dict(exclude_none=True),
            VARIANT_DATA_ROW.dict(exclude_none=True),
            VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.dict(exclude_none=True),
            VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.dict(exclude_none=True),
            VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.dict(exclude_none=True),
            VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.dict(exclude_none=True),
            CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW.dict(exclude_none=True),
        ]
        DAILY_EXPOSURES_DATA = [
            EXPOSURES_CONTROL_DATA_ROW.dict(exclude_none=True),
            EXPOSURES_VARIANT_DATA_ROW.dict(exclude_none=True),
            EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.dict(exclude_none=True),
            EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.dict(exclude_none=True),
        ]
        SEGMENT_DATA = [
            SEGMENTED_ROW_VARIANT.dict(exclude_none=True),
            SEGMENTED_ROW_CONTROL.dict(exclude_none=True),
        ]
        SEGMENT_EXPOSURES_DATA = [
            EXPOSURES_SEGMENTED_ROW_VARIANT.dict(exclude_none=True),
            EXPOSURES_SEGMENTED_ROW_CONTROL.dict(exclude_none=True),
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
            DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL_CONTROL,
            DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL_VARIANT,
            DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE_CONTROL,
            DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE_VARIANT,
            DIFFERENCE_METRIC_DATA_WEEKLY_NEGATIVE_CONTROL,
            DIFFERENCE_METRIC_DATA_WEEKLY_NEGATIVE_VARIANT,
            DIFFERENCE_METRIC_DATA_OVERALL_NEUTRAL_CONTROL,
            DIFFERENCE_METRIC_DATA_OVERALL_NEUTRAL_VARIANT,
            DIFFERENCE_METRIC_DATA_OVERALL_POSITIVE_CONTROL,
            DIFFERENCE_METRIC_DATA_OVERALL_POSITIVE_VARIANT,
            DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE_CONTROL,
            DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE_VARIANT,
        ) = cls.get_differences(
            DATA_POINT_A,
            DATA_POINT_F,
            DATA_POINT_B,
            DATA_POINT_E,
            DATA_POINT_C,
            DATA_POINT_D,
        )

        PairwiseBranchComparisonData = cls.get_pairwise_branch_comparison_data()
        PairwiseSignificanceData = cls.get_pairwise_significance_data()

        EMPTY_METRIC_DATA = MetricData(
            absolute=BranchComparisonData(),
            difference=PairwiseBranchComparisonData(),
            relative_uplift=PairwiseBranchComparisonData(),
            significance=PairwiseSignificanceData(),
        )

        WEEKLY_BASE = {
            "control": {
                "is_control": True,
                "branch_data": {
                    Group.SEARCH.value: {
                        "search_count": EMPTY_METRIC_DATA.dict(exclude_none=True),
                    },
                    Group.USAGE.value: {},
                    Group.OTHER.value: {
                        "identity": ABSOLUTE_METRIC_DATA_A.dict(exclude_none=True),
                        "some_count": EMPTY_METRIC_DATA.dict(exclude_none=True),
                        "another_count": EMPTY_METRIC_DATA.dict(exclude_none=True),
                        "retained": DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL_VARIANT.dict(
                            exclude_none=True
                        ),
                    },
                },
            },
            "variant": {
                "is_control": False,
                "branch_data": {
                    Group.SEARCH.value: {
                        "search_count": (
                            DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE_CONTROL.dict(
                                exclude_none=True
                            )
                        ),
                    },
                    Group.USAGE.value: {},
                    Group.OTHER.value: {
                        "identity": ABSOLUTE_METRIC_DATA_A.dict(exclude_none=True),
                        "some_count": ABSOLUTE_METRIC_DATA_A.dict(exclude_none=True),
                        "another_count": ABSOLUTE_METRIC_DATA_A.dict(exclude_none=True),
                        "retained": DIFFERENCE_METRIC_DATA_WEEKLY_NEGATIVE_CONTROL.dict(
                            exclude_none=True
                        ),
                    },
                },
            },
        }

        WEEKLY_EXPOSURES_DATA = deepcopy(WEEKLY_BASE)
        del WEEKLY_EXPOSURES_DATA["control"]["branch_data"][Group.OTHER]["retained"]
        del WEEKLY_EXPOSURES_DATA["variant"]["branch_data"][Group.OTHER]["retained"]
        del WEEKLY_EXPOSURES_DATA["control"]["branch_data"][Group.SEARCH]["search_count"]
        del WEEKLY_EXPOSURES_DATA["variant"]["branch_data"][Group.SEARCH]["search_count"]

        WEEKLY_SEGMENT_DATA = deepcopy(WEEKLY_EXPOSURES_DATA)
        del WEEKLY_SEGMENT_DATA["control"]["branch_data"][Group.OTHER]["another_count"]
        del WEEKLY_SEGMENT_DATA["variant"]["branch_data"][Group.OTHER]["another_count"]
        del WEEKLY_SEGMENT_DATA["control"]["branch_data"][Group.OTHER]["some_count"]
        del WEEKLY_SEGMENT_DATA["variant"]["branch_data"][Group.OTHER]["some_count"]

        WEEKLY_DATA = {
            "enrollments": {
                "all": WEEKLY_BASE,
                "some_segment": WEEKLY_SEGMENT_DATA,
            },
            "exposures": {
                "all": WEEKLY_EXPOSURES_DATA,
                "some_segment": WEEKLY_SEGMENT_DATA,
            },
        }

        OVERALL_BASE = {
            "control": {
                "is_control": True,
                "branch_data": {
                    Group.SEARCH.value: {
                        "search_count": EMPTY_METRIC_DATA.dict(exclude_none=True),
                    },
                    Group.USAGE.value: {},
                    Group.OTHER.value: {
                        "identity": ABSOLUTE_METRIC_DATA_F_WITH_PERCENT.dict(
                            exclude_none=True
                        ),
                        "some_count": EMPTY_METRIC_DATA.dict(exclude_none=True),
                        "another_count": EMPTY_METRIC_DATA.dict(exclude_none=True),
                        "retained": DIFFERENCE_METRIC_DATA_OVERALL_NEUTRAL_VARIANT.dict(
                            exclude_none=True
                        ),
                    },
                },
            },
            "variant": {
                "is_control": False,
                "branch_data": {
                    Group.SEARCH.value: {
                        "search_count": (
                            DIFFERENCE_METRIC_DATA_OVERALL_POSITIVE_CONTROL.dict(
                                exclude_none=True
                            )
                        ),
                    },
                    Group.USAGE.value: {},
                    Group.OTHER.value: {
                        "identity": ABSOLUTE_METRIC_DATA_F_WITH_PERCENT.dict(
                            exclude_none=True
                        ),
                        "some_count": ABSOLUTE_METRIC_DATA_F.dict(exclude_none=True),
                        "another_count": ABSOLUTE_METRIC_DATA_F.dict(exclude_none=True),
                        "retained": DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE_CONTROL.dict(
                            exclude_none=True
                        ),
                    },
                },
            },
        }

        OVERALL_EXPOSURES_DATA = deepcopy(OVERALL_BASE)
        del OVERALL_EXPOSURES_DATA["control"]["branch_data"][Group.OTHER]["retained"]
        del OVERALL_EXPOSURES_DATA["variant"]["branch_data"][Group.OTHER]["retained"]
        del OVERALL_EXPOSURES_DATA["control"]["branch_data"][Group.SEARCH]["search_count"]
        del OVERALL_EXPOSURES_DATA["variant"]["branch_data"][Group.SEARCH]["search_count"]

        OVERALL_SEGMENT_DATA = deepcopy(OVERALL_EXPOSURES_DATA)
        del OVERALL_SEGMENT_DATA["control"]["branch_data"][Group.OTHER]["another_count"]
        del OVERALL_SEGMENT_DATA["variant"]["branch_data"][Group.OTHER]["another_count"]
        del OVERALL_SEGMENT_DATA["control"]["branch_data"][Group.OTHER]["some_count"]
        del OVERALL_SEGMENT_DATA["variant"]["branch_data"][Group.OTHER]["some_count"]

        OVERALL_DATA = {
            "enrollments": {
                "all": OVERALL_BASE,
                "some_segment": OVERALL_SEGMENT_DATA,
            },
            "exposures": {
                "all": OVERALL_EXPOSURES_DATA,
                "some_segment": OVERALL_SEGMENT_DATA,
            },
        }

        ERRORS = {
            "experiment": [],
        }

        cls.add_all_outcome_data(
            DAILY_DATA,
            OVERALL_DATA,
            WEEKLY_DATA,
            primary_outcomes,
            AnalysisBasis.ENROLLMENTS,
        )
        cls.add_all_outcome_data(
            DAILY_EXPOSURES_DATA,
            OVERALL_DATA,
            WEEKLY_DATA,
            primary_outcomes,
            AnalysisBasis.EXPOSURES,
        )

        return (
            DAILY_DATA,
            WEEKLY_DATA,
            OVERALL_DATA,
            ERRORS,
            SEGMENT_DATA,
            DAILY_EXPOSURES_DATA,
            SEGMENT_EXPOSURES_DATA,
        )


class ZeroJetstreamTestData(JetstreamTestData):
    @classmethod
    def get_identity_row(cls):
        return JetstreamDataPoint(
            point=0,
            upper=0,
            lower=0,
            branch="control",
            metric=Metric.USER_COUNT,
            statistic=Statistic.COUNT,
            window_index="1",
            segment=Segment.ALL,
            analysis_basis=AnalysisBasis.ENROLLMENTS,
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
        CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW.comparison_to_branch = "variant"

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
        DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL_CONTROL = cls.get_difference_metric_data(
            DATA_POINT_B,
            SignificanceData(weekly={}, overall={}),
            comparison_to_branch="control",
        )
        DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE_CONTROL = cls.get_difference_metric_data(
            DATA_POINT_A,
            SignificanceData(weekly={}, overall={}),
            comparison_to_branch="control",
        )
        DIFFERENCE_METRIC_DATA_WEEKLY_NEGATIVE_CONTROL = cls.get_difference_metric_data(
            DATA_POINT_C,
            SignificanceData(weekly={}, overall={}),
            comparison_to_branch="control",
        )
        DIFFERENCE_METRIC_DATA_OVERALL_NEUTRAL_CONTROL = cls.get_difference_metric_data(
            DATA_POINT_E,
            SignificanceData(weekly={}, overall={}),
            comparison_to_branch="control",
        )
        DIFFERENCE_METRIC_DATA_OVERALL_POSITIVE_CONTROL = cls.get_difference_metric_data(
            DATA_POINT_F,
            SignificanceData(weekly={}, overall={}),
            comparison_to_branch="control",
        )
        DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE_CONTROL = cls.get_difference_metric_data(
            DATA_POINT_D,
            SignificanceData(weekly={}, overall={}),
            comparison_to_branch="control",
        )
        DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL_VARIANT = cls.get_difference_metric_data(
            DATA_POINT_B,
            SignificanceData(weekly={}, overall={}),
            comparison_to_branch="variant",
        )
        DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE_VARIANT = cls.get_difference_metric_data(
            DATA_POINT_A,
            SignificanceData(weekly={}, overall={}),
            comparison_to_branch="variant",
        )
        DIFFERENCE_METRIC_DATA_WEEKLY_NEGATIVE_VARIANT = cls.get_difference_metric_data(
            DATA_POINT_C,
            SignificanceData(weekly={}, overall={}),
            comparison_to_branch="variant",
        )
        DIFFERENCE_METRIC_DATA_OVERALL_NEUTRAL_VARIANT = cls.get_difference_metric_data(
            DATA_POINT_E,
            SignificanceData(weekly={}, overall={}),
            comparison_to_branch="variant",
        )
        DIFFERENCE_METRIC_DATA_OVERALL_POSITIVE_VARIANT = cls.get_difference_metric_data(
            DATA_POINT_F,
            SignificanceData(weekly={}, overall={}),
            comparison_to_branch="variant",
        )
        DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE_VARIANT = cls.get_difference_metric_data(
            DATA_POINT_D,
            SignificanceData(weekly={}, overall={}),
            comparison_to_branch="variant",
        )

        return (
            DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL_CONTROL,
            DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL_VARIANT,
            DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE_CONTROL,
            DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE_VARIANT,
            DIFFERENCE_METRIC_DATA_WEEKLY_NEGATIVE_CONTROL,
            DIFFERENCE_METRIC_DATA_WEEKLY_NEGATIVE_VARIANT,
            DIFFERENCE_METRIC_DATA_OVERALL_NEUTRAL_CONTROL,
            DIFFERENCE_METRIC_DATA_OVERALL_NEUTRAL_VARIANT,
            DIFFERENCE_METRIC_DATA_OVERALL_POSITIVE_CONTROL,
            DIFFERENCE_METRIC_DATA_OVERALL_POSITIVE_VARIANT,
            DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE_CONTROL,
            DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE_VARIANT,
        )

    @classmethod
    def add_outcome_data(
        cls, data, overall_data, weekly_data, primary_outcome, analysis_basis
    ):
        primary_metrics = ["default_browser_action"]
        range_data = DataPoint(lower=0, point=0, upper=0)

        for primary_metric in primary_metrics:
            for branch in DEFAULT_TEST_BRANCHES:
                if Group.OTHER not in overall_data[branch]["branch_data"]:
                    overall_data[branch]["branch_data"][Group.OTHER.value] = {}
                if Group.OTHER not in weekly_data[branch]["branch_data"]:
                    weekly_data[branch]["branch_data"][Group.OTHER.value] = {}

                data_point_overall = range_data.copy()
                data_point_overall.count = 0.0
                overall_data[branch]["branch_data"][Group.OTHER.value][
                    primary_metric
                ] = cls.get_metric_data(data_point_overall)

                data_point_weekly = range_data.copy()
                data_point_weekly.window_index = "1"
                weekly_data[branch]["branch_data"][Group.OTHER.value][
                    primary_metric
                ] = cls.get_metric_data(data_point_weekly)

                data.append(
                    JetstreamDataPoint(
                        **range_data.dict(exclude_none=True),
                        metric=primary_metric,
                        branch=branch,
                        statistic="binomial",
                        window_index="1",
                        segment=Segment.ALL,
                        analysis_basis=analysis_basis,
                    ).dict(exclude_none=True)
                )


class NonePointJetstreamTestData(ZeroJetstreamTestData):
    @classmethod
    def get_identity_row(cls):
        return JetstreamDataPoint(
            point=None,
            upper=None,
            lower=None,
            branch="control",
            metric=Metric.USER_COUNT,
            statistic=Statistic.COUNT,
            window_index=None,
            segment=Segment.ALL,
            analysis_basis=AnalysisBasis.ENROLLMENTS,
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
