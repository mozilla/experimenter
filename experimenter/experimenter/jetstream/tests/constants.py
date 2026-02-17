from copy import deepcopy
from functools import cache

from pydantic import Field, create_model

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
        return cls.get_pairwise_metric_data()(
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

        significance = cls.get_pairwise_significance_data()().model_dump()
        difference = cls.get_pairwise_branch_comparison_data()().model_dump()

        # initialize pairwise branch comparisons inside dicts
        for branch in branches:
            significance[branch] = SignificanceData().model_dump()
            difference[branch] = BranchComparisonData().model_dump()

        # set the comparison branch's data
        comparison_data = BranchComparisonData(
            first=DATA_POINT, all=all_data_points
        ).model_dump()
        significance[comparison_to_branch] = deepcopy(SIGNIFICANCE.model_dump())
        difference[comparison_to_branch] = comparison_data

        return cls.get_pairwise_metric_data()(
            absolute=BranchComparisonData(),
            difference=cls.get_pairwise_branch_comparison_data()(**difference),
            relative_uplift=cls.get_pairwise_branch_comparison_data()(),
            significance=cls.get_pairwise_significance_data()(**significance),
        )

    @classmethod
    @cache
    def get_pairwise_branch_comparison_data(cls, branches=None):
        if not branches:
            branches = DEFAULT_TEST_BRANCHES
        return create_model(
            "PairwiseBranchComparisonData",
            **{
                branch: (
                    BranchComparisonData,
                    Field(default_factory=BranchComparisonData),
                )
                for branch in branches
            },
        )

    @classmethod
    @cache
    def get_pairwise_significance_data(cls, branches=None):
        if not branches:
            branches = DEFAULT_TEST_BRANCHES
        # create a dynamic model that extends SignificanceData with all branches
        return create_model(
            "PairwiseSignificanceData",
            **{
                branch: (SignificanceData, Field(default_factory=SignificanceData))
                for branch in branches
            },
        )

    @classmethod
    @cache
    def get_pairwise_metric_data(cls):
        PairwiseBranchComparisonData = cls.get_pairwise_branch_comparison_data()
        PairwiseSignificanceData = cls.get_pairwise_significance_data()

        class PairwiseMetricData(MetricData):
            difference: PairwiseBranchComparisonData
            relative_uplift: PairwiseBranchComparisonData
            significance: PairwiseSignificanceData

        return PairwiseMetricData

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
            VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.model_copy()
        )
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.point = -2.0
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.upper = -1.0
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.lower = -5.0
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.metric = Metric.RETENTION
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.statistic = Statistic.BINOMIAL

        CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW = (
            VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.model_copy()
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
        DATA_POINT_F = DATA_POINT_A.model_copy()
        DATA_POINT_F.window_index = None
        DATA_POINT_A_COVARIATE = DATA_POINT_A.model_copy()
        DATA_POINT_A_COVARIATE.point = 11.5
        DATA_POINT_F_COVARIATE = DATA_POINT_F.model_copy()
        DATA_POINT_F_COVARIATE.point = 11.5

        DATA_POINT_B = DataPoint(lower=-5, point=12, upper=13, window_index=1)
        DATA_POINT_E = DATA_POINT_B.model_copy()
        DATA_POINT_E.window_index = None

        DATA_POINT_C = DataPoint(lower=-5, point=-2, upper=-1, window_index=1)
        DATA_POINT_D = DATA_POINT_C.model_copy()
        DATA_POINT_D.window_index = None

        ABSOLUTE_METRIC_DATA_A = cls.get_absolute_metric_data(DATA_POINT_A)
        ABSOLUTE_METRIC_DATA_F = cls.get_absolute_metric_data(DATA_POINT_F)
        ABSOLUTE_METRIC_DATA_F_WITH_PERCENT = ABSOLUTE_METRIC_DATA_F.model_copy()
        ABSOLUTE_METRIC_DATA_F_WITH_PERCENT.percent = 50.0

        ABSOLUTE_METRIC_DATA_A_COVARIATE = cls.get_absolute_metric_data(
            DATA_POINT_A_COVARIATE
        )
        ABSOLUTE_METRIC_DATA_F_COVARIATE = cls.get_absolute_metric_data(
            DATA_POINT_F_COVARIATE
        )
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
            ABSOLUTE_METRIC_DATA_A_COVARIATE,
            ABSOLUTE_METRIC_DATA_F_COVARIATE,
            DATA_POINT_A_COVARIATE,
            DATA_POINT_F_COVARIATE,
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
        DATA_POINT_A_COVARIATE,
        DATA_POINT_F_COVARIATE,
    ):
        DIFFERENCE_METRIC_DATA_DAILY_NEUTRAL_CONTROL = cls.get_difference_metric_data(
            DATA_POINT_D,
            SignificanceData(
                daily={"1": Significance.NEUTRAL.value}, weekly={}, overall={}
            ),
            comparison_to_branch="control",
        )
        DIFFERENCE_METRIC_DATA_DAILY_POSITIVE_CONTROL = cls.get_difference_metric_data(
            DATA_POINT_F_COVARIATE,
            SignificanceData(
                daily={"1": Significance.POSITIVE.value}, weekly={}, overall={}
            ),
            comparison_to_branch="control",
        )
        DIFFERENCE_METRIC_DATA_DAILY_NEGATIVE_CONTROL = cls.get_difference_metric_data(
            DATA_POINT_D,
            SignificanceData(
                daily={"1": Significance.NEGATIVE.value}, weekly={}, overall={}
            ),
            comparison_to_branch="control",
        )
        DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL_CONTROL = cls.get_difference_metric_data(
            DATA_POINT_B,
            SignificanceData(weekly={"1": Significance.NEUTRAL.value}, overall={}),
            comparison_to_branch="control",
        )
        DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE_CONTROL = cls.get_difference_metric_data(
            DATA_POINT_A_COVARIATE,
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
            DATA_POINT_F_COVARIATE,
            SignificanceData(weekly={}, overall={"1": Significance.POSITIVE.value}),
            comparison_to_branch="control",
        )
        DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE_CONTROL = cls.get_difference_metric_data(
            DATA_POINT_D,
            SignificanceData(weekly={}, overall={"1": Significance.NEGATIVE.value}),
            is_retention=True,
            comparison_to_branch="control",
        )
        DIFFERENCE_METRIC_DATA_DAILY_NEUTRAL_VARIANT = cls.get_difference_metric_data(
            DATA_POINT_E,
            SignificanceData(
                daily={"1": Significance.NEUTRAL.value}, weekly={}, overall={}
            ),
            comparison_to_branch="variant",
        )
        DIFFERENCE_METRIC_DATA_DAILY_POSITIVE_VARIANT = cls.get_difference_metric_data(
            DATA_POINT_F,
            SignificanceData(
                daily={"1": Significance.POSITIVE.value}, weekly={}, overall={}
            ),
            comparison_to_branch="variant",
        )
        DIFFERENCE_METRIC_DATA_DAILY_NEGATIVE_VARIANT = cls.get_difference_metric_data(
            DATA_POINT_D,
            SignificanceData(
                daily={"1": Significance.NEGATIVE.value}, weekly={}, overall={}
            ),
            comparison_to_branch="variant",
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
            is_retention=True,
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
            DIFFERENCE_METRIC_DATA_DAILY_NEUTRAL_VARIANT,
            DIFFERENCE_METRIC_DATA_DAILY_NEUTRAL_CONTROL,
            DIFFERENCE_METRIC_DATA_DAILY_POSITIVE_VARIANT,
            DIFFERENCE_METRIC_DATA_DAILY_POSITIVE_CONTROL,
            DIFFERENCE_METRIC_DATA_DAILY_NEGATIVE_VARIANT,
            DIFFERENCE_METRIC_DATA_DAILY_NEGATIVE_CONTROL,
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
        return cls.get_pairwise_metric_data()(
            absolute=BranchComparisonData(first=data_point, all=[data_point]),
            difference=cls.get_pairwise_branch_comparison_data()(),
            relative_uplift=cls.get_pairwise_branch_comparison_data()(),
            significance=cls.get_pairwise_significance_data()(),
        ).model_dump(exclude_none=True)

    @classmethod
    def add_outcome_data(
        cls,
        data,
        formatted_daily_data,
        overall_data,
        weekly_data,
        primary_outcome,
        analysis_basis,
    ):
        primary_metrics = ["default_browser_action"]
        range_data = DataPoint(lower=2, point=4, upper=8)

        for primary_metric in primary_metrics:
            for branch in DEFAULT_TEST_BRANCHES:
                if Group.OTHER not in overall_data[branch]["branch_data"]:
                    overall_data[branch]["branch_data"][Group.OTHER.value] = {}
                if Group.OTHER not in weekly_data[branch]["branch_data"]:
                    weekly_data[branch]["branch_data"][Group.OTHER.value] = {}
                if Group.OTHER not in formatted_daily_data[branch]["branch_data"]:
                    formatted_daily_data[branch]["branch_data"][Group.OTHER.value] = {}

                data_point_overall = range_data.model_copy()
                data_point_overall.count = 48.0
                overall_data[branch]["branch_data"][Group.OTHER.value][primary_metric] = (
                    cls.get_metric_data(data_point_overall)
                )

                data_point_weekly = range_data.model_copy()
                data_point_weekly.window_index = "1"
                weekly_data[branch]["branch_data"][Group.OTHER.value][primary_metric] = (
                    cls.get_metric_data(data_point_weekly)
                )

                data_point_daily = range_data.model_copy()
                formatted_daily_data[branch]["branch_data"][Group.OTHER.value][
                    primary_metric
                ] = cls.get_metric_data(data_point_daily)

                data.append(
                    JetstreamDataPoint(
                        **range_data.model_dump(exclude_none=True),
                        metric=primary_metric,
                        branch=branch,
                        statistic="binomial",
                        window_index="1",
                        segment=Segment.ALL,
                        analysis_basis=analysis_basis,
                    ).model_dump(exclude_none=True)
                )

    @classmethod
    def add_outcome_data_mean(
        cls,
        data,
        formatted_daily_data,
        overall_data,
        weekly_data,
        primary_outcome,
        analysis_basis,
    ):
        primary_metrics = ["mozilla_default_browser"]
        range_data = DataPoint(lower=0, point=0, upper=0)

        for primary_metric in primary_metrics:
            for branch in DEFAULT_TEST_BRANCHES:
                if Group.OTHER not in overall_data[branch]["branch_data"]:
                    overall_data[branch]["branch_data"][Group.OTHER.value] = {}
                if Group.OTHER not in weekly_data[branch]["branch_data"]:
                    weekly_data[branch]["branch_data"][Group.OTHER.value] = {}
                if Group.OTHER not in formatted_daily_data[branch]["branch_data"]:
                    formatted_daily_data[branch]["branch_data"][Group.OTHER.value] = {}

                data_point_overall = range_data.model_copy()
                data_point_overall.count = 0.0
                overall_data[branch]["branch_data"][Group.OTHER.value][primary_metric] = (
                    cls.get_metric_data(data_point_overall)
                )

                data_point_weekly = range_data.model_copy()
                data_point_weekly.window_index = "1"
                weekly_data[branch]["branch_data"][Group.OTHER.value][primary_metric] = (
                    cls.get_metric_data(data_point_weekly)
                )

                data_point_daily = range_data.model_copy()
                formatted_daily_data[branch]["branch_data"][Group.OTHER.value][
                    primary_metric
                ] = cls.get_metric_data(data_point_daily)

                data.append(
                    JetstreamDataPoint(
                        **range_data.model_dump(exclude_none=True),
                        metric=primary_metric,
                        branch=branch,
                        statistic="mean",
                        window_index="1",
                        segment=Segment.ALL,
                        analysis_basis=analysis_basis,
                    ).model_dump(exclude_none=True)
                )

    @classmethod
    def add_all_outcome_data(
        cls,
        data,
        formatted_daily_data,
        overall_data,
        weekly_data,
        primary_outcomes,
        analysis_basis,
    ):
        for primary_outcome in primary_outcomes:
            cls.add_outcome_data(
                data,
                formatted_daily_data,
                overall_data,
                weekly_data,
                primary_outcome,
                analysis_basis,
            )

            cls.add_outcome_data_mean(
                data,
                formatted_daily_data,
                overall_data,
                weekly_data,
                primary_outcome,
                analysis_basis,
            )

    @classmethod
    def get_test_data(cls, primary_outcomes):
        DATA_IDENTITY_ROW = cls.get_identity_row()

        CONTROL_DATA_ROW = DATA_IDENTITY_ROW.model_copy()
        CONTROL_DATA_ROW.branch = "control"

        VARIANT_DATA_ROW = DATA_IDENTITY_ROW.model_copy()
        VARIANT_DATA_ROW.branch = "variant"

        SEGMENTED_ROW_VARIANT = VARIANT_DATA_ROW.model_copy()
        SEGMENTED_ROW_VARIANT.segment = "some_segment"
        SEGMENTED_ROW_CONTROL = CONTROL_DATA_ROW.model_copy()
        SEGMENTED_ROW_CONTROL.segment = "some_segment"

        VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN = DATA_IDENTITY_ROW.model_copy()
        VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.metric = "some_count"
        VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.statistic = Statistic.MEAN
        VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.branch = "variant"

        VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN_LM = DATA_IDENTITY_ROW.model_copy()
        VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN_LM.metric = "some_count"
        VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN_LM.point = 11.5
        VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN_LM.statistic = Statistic.LINEAR_MODEL_MEAN
        VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN_LM.branch = "variant"

        VARIANT_DATA_DEFAULT_METRIC_ROW_RATIO = DATA_IDENTITY_ROW.model_copy()
        VARIANT_DATA_DEFAULT_METRIC_ROW_RATIO.metric = "some_ratio"
        VARIANT_DATA_DEFAULT_METRIC_ROW_RATIO.statistic = Statistic.POPULATION_RATIO
        VARIANT_DATA_DEFAULT_METRIC_ROW_RATIO.branch = "variant"

        VARIANT_DATA_DEFAULT_METRIC_ROW_DAU_IMPACT = DATA_IDENTITY_ROW.model_copy()
        VARIANT_DATA_DEFAULT_METRIC_ROW_DAU_IMPACT.metric = "some_dau_impact"
        VARIANT_DATA_DEFAULT_METRIC_ROW_DAU_IMPACT.statistic = (
            Statistic.PER_CLIENT_DAU_IMPACT
        )
        VARIANT_DATA_DEFAULT_METRIC_ROW_DAU_IMPACT.branch = "variant"

        VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL = DATA_IDENTITY_ROW.model_copy()
        VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.metric = "another_count"
        VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.statistic = Statistic.BINOMIAL
        VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.branch = "variant"

        VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW = DATA_IDENTITY_ROW.model_copy()
        VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.comparison = BranchComparison.DIFFERENCE
        VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.metric = Metric.SEARCH
        VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.statistic = Statistic.MEAN
        VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.branch = "variant"
        VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.comparison_to_branch = "control"

        VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW_MEAN_LM = (
            VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.model_copy()
        )
        VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW_MEAN_LM.statistic = (
            Statistic.LINEAR_MODEL_MEAN
        )
        VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW_MEAN_LM.point = 11.5

        BROKEN_STATISTIC_DATA_ROW = CONTROL_DATA_ROW.model_copy()
        BROKEN_STATISTIC_DATA_ROW.comparison = BranchComparison.ABSOLUTE
        BROKEN_STATISTIC_DATA_ROW.metric = "custom_metric"
        BROKEN_STATISTIC_DATA_ROW.statistic = "something_else"

        VARIANT_BROKEN_STATISTIC_DATA_ROW = VARIANT_DATA_ROW.model_copy()
        VARIANT_BROKEN_STATISTIC_DATA_ROW.comparison = BranchComparison.ABSOLUTE
        VARIANT_BROKEN_STATISTIC_DATA_ROW.metric = "custom_metric"
        VARIANT_BROKEN_STATISTIC_DATA_ROW.statistic = "something_else"

        EXPOSURES_BROKEN_STATISTIC_DATA_ROW = BROKEN_STATISTIC_DATA_ROW.model_copy()
        EXPOSURES_BROKEN_STATISTIC_DATA_ROW.analysis_basis = AnalysisBasis.EXPOSURES

        VARIANT_EXPOSURES_BROKEN_STATISTIC_DATA_ROW = (
            VARIANT_BROKEN_STATISTIC_DATA_ROW.model_copy()
        )
        VARIANT_EXPOSURES_BROKEN_STATISTIC_DATA_ROW.analysis_basis = (
            AnalysisBasis.EXPOSURES
        )

        (
            VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW,
            CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW,
        ) = cls.get_significance_data_row(VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW)

        # exposures
        EXPOSURES_CONTROL_DATA_ROW = DATA_IDENTITY_ROW.model_copy()
        EXPOSURES_CONTROL_DATA_ROW.branch = "control"
        EXPOSURES_CONTROL_DATA_ROW.analysis_basis = AnalysisBasis.EXPOSURES

        EXPOSURES_VARIANT_DATA_ROW = DATA_IDENTITY_ROW.model_copy()
        EXPOSURES_VARIANT_DATA_ROW.branch = "variant"
        EXPOSURES_VARIANT_DATA_ROW.analysis_basis = AnalysisBasis.EXPOSURES

        EXPOSURES_SEGMENTED_ROW_VARIANT = VARIANT_DATA_ROW.model_copy()
        EXPOSURES_SEGMENTED_ROW_VARIANT.segment = "some_segment"
        EXPOSURES_SEGMENTED_ROW_VARIANT.analysis_basis = AnalysisBasis.EXPOSURES
        EXPOSURES_SEGMENTED_ROW_CONTROL = CONTROL_DATA_ROW.model_copy()
        EXPOSURES_SEGMENTED_ROW_CONTROL.segment = "some_segment"
        EXPOSURES_SEGMENTED_ROW_CONTROL.analysis_basis = AnalysisBasis.EXPOSURES

        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN = DATA_IDENTITY_ROW.model_copy()
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.metric = "some_count"
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.statistic = Statistic.MEAN
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.branch = "variant"
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.analysis_basis = (
            AnalysisBasis.EXPOSURES
        )

        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN_LM = DATA_IDENTITY_ROW.model_copy()
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN_LM.metric = "some_count"
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN_LM.point = 11.5
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN_LM.statistic = (
            Statistic.LINEAR_MODEL_MEAN
        )
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN_LM.branch = "variant"
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN_LM.analysis_basis = (
            AnalysisBasis.EXPOSURES
        )

        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_RATIO = DATA_IDENTITY_ROW.model_copy()
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_RATIO.metric = "some_ratio"
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_RATIO.statistic = (
            Statistic.POPULATION_RATIO
        )
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_RATIO.branch = "variant"
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_RATIO.analysis_basis = (
            AnalysisBasis.EXPOSURES
        )

        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_DAU_IMPACT = (
            DATA_IDENTITY_ROW.model_copy()
        )
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_DAU_IMPACT.metric = "some_dau_impact"
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_DAU_IMPACT.statistic = (
            Statistic.PER_CLIENT_DAU_IMPACT
        )
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_DAU_IMPACT.branch = "variant"
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_DAU_IMPACT.analysis_basis = (
            AnalysisBasis.EXPOSURES
        )

        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL = (
            DATA_IDENTITY_ROW.model_copy()
        )
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.metric = "another_count"
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.statistic = Statistic.BINOMIAL
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.branch = "variant"
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.analysis_basis = (
            AnalysisBasis.EXPOSURES
        )

        EXPOSURES_VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW = DATA_IDENTITY_ROW.model_copy()
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

        EXPOSURES_VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW_MEAN_LM = (
            EXPOSURES_VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.model_copy()
        )
        EXPOSURES_VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW_MEAN_LM.statistic = (
            Statistic.LINEAR_MODEL_MEAN
        )
        EXPOSURES_VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW_MEAN_LM.point = 11.5

        (
            EXPOSURES_VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW,
            EXPOSURES_CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW,
        ) = cls.get_significance_data_row(
            EXPOSURES_VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW
        )

        DAILY_DATA = [
            CONTROL_DATA_ROW.model_dump(exclude_none=True),
            VARIANT_DATA_ROW.model_dump(exclude_none=True),
            VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.model_dump(exclude_none=True),
            VARIANT_DATA_DEFAULT_METRIC_ROW_RATIO.model_dump(exclude_none=True),
            VARIANT_DATA_DEFAULT_METRIC_ROW_DAU_IMPACT.model_dump(exclude_none=True),
            VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.model_dump(exclude_none=True),
            VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.model_dump(exclude_none=True),
            VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.model_dump(exclude_none=True),
            CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW.model_dump(exclude_none=True),
            BROKEN_STATISTIC_DATA_ROW.model_dump(exclude_none=True),
            VARIANT_BROKEN_STATISTIC_DATA_ROW.model_dump(exclude_none=True),
        ]
        DAILY_EXPOSURES_DATA = [
            EXPOSURES_CONTROL_DATA_ROW.model_dump(exclude_none=True),
            EXPOSURES_VARIANT_DATA_ROW.model_dump(exclude_none=True),
            EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.model_dump(exclude_none=True),
            EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_RATIO.model_dump(exclude_none=True),
            EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_DAU_IMPACT.model_dump(
                exclude_none=True
            ),
            EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.model_dump(
                exclude_none=True
            ),
            EXPOSURES_VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.model_dump(
                exclude_none=True
            ),
            EXPOSURES_VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.model_dump(
                exclude_none=True
            ),
            EXPOSURES_CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW.model_dump(exclude_none=True),
            EXPOSURES_BROKEN_STATISTIC_DATA_ROW.model_dump(exclude_none=True),
            VARIANT_EXPOSURES_BROKEN_STATISTIC_DATA_ROW.model_dump(exclude_none=True),
        ]
        if cls == JetstreamTestData:
            # don't test that the mean_lm (covariate adjusted) stat
            # supercedes the mean stat for non-JetstreamTestData classes
            DAILY_DATA.extend(
                [
                    VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN_LM.model_dump(exclude_none=True),
                    VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW_MEAN_LM.model_dump(
                        exclude_none=True
                    ),
                ]
            )
            DAILY_EXPOSURES_DATA.extend(
                [
                    EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN_LM.model_dump(
                        exclude_none=True
                    ),
                    EXPOSURES_VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW_MEAN_LM.model_dump(
                        exclude_none=True
                    ),
                ]
            )

        SEGMENT_DATA = [
            SEGMENTED_ROW_VARIANT.model_dump(exclude_none=True),
            SEGMENTED_ROW_CONTROL.model_dump(exclude_none=True),
        ]
        SEGMENT_EXPOSURES_DATA = [
            EXPOSURES_SEGMENTED_ROW_VARIANT.model_dump(exclude_none=True),
            EXPOSURES_SEGMENTED_ROW_CONTROL.model_dump(exclude_none=True),
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
            ABSOLUTE_METRIC_DATA_A_COVARIATE,
            ABSOLUTE_METRIC_DATA_F_COVARIATE,
            DATA_POINT_A_COVARIATE,
            DATA_POINT_F_COVARIATE,
        ) = cls.get_data_points()

        (
            DIFFERENCE_METRIC_DATA_DAILY_NEUTRAL_VARIANT,
            DIFFERENCE_METRIC_DATA_DAILY_NEUTRAL_CONTROL,
            DIFFERENCE_METRIC_DATA_DAILY_POSITIVE_VARIANT,
            DIFFERENCE_METRIC_DATA_DAILY_POSITIVE_CONTROL,
            DIFFERENCE_METRIC_DATA_DAILY_NEGATIVE_VARIANT,
            DIFFERENCE_METRIC_DATA_DAILY_NEGATIVE_CONTROL,
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
            DATA_POINT_A_COVARIATE,
            DATA_POINT_F_COVARIATE,
        )

        PairwiseBranchComparisonData = cls.get_pairwise_branch_comparison_data()
        PairwiseSignificanceData = cls.get_pairwise_significance_data()

        EMPTY_METRIC_DATA = cls.get_pairwise_metric_data()(
            absolute=BranchComparisonData(),
            difference=PairwiseBranchComparisonData(),
            relative_uplift=PairwiseBranchComparisonData(),
            significance=PairwiseSignificanceData(),
        )

        FORMATTED_DAILY_DATA = {
            "control": {
                "is_control": True,
                "branch_data": {
                    Group.SEARCH.value: {
                        "search_count": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                    },
                    Group.USAGE.value: {},
                    Group.OTHER.value: {
                        "identity": ABSOLUTE_METRIC_DATA_F.model_dump(exclude_none=True),
                        "some_count": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                        "some_ratio": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                        "some_dau_impact": EMPTY_METRIC_DATA.model_dump(
                            exclude_none=True
                        ),
                        "another_count": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                        "retained": (
                            DIFFERENCE_METRIC_DATA_DAILY_NEUTRAL_VARIANT.model_dump(
                                exclude_none=True
                            )
                        ),
                        "custom_metric": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                    },
                },
            },
            "variant": {
                "is_control": False,
                "branch_data": {
                    Group.SEARCH.value: {
                        "search_count": (
                            DIFFERENCE_METRIC_DATA_DAILY_POSITIVE_CONTROL.model_dump(
                                exclude_none=True
                            )
                        ),
                    },
                    Group.USAGE.value: {},
                    Group.OTHER.value: {
                        "identity": ABSOLUTE_METRIC_DATA_F.model_dump(exclude_none=True),
                        "some_count": ABSOLUTE_METRIC_DATA_F_COVARIATE.model_dump(
                            exclude_none=True
                        ),
                        "some_ratio": ABSOLUTE_METRIC_DATA_F.model_dump(
                            exclude_none=True
                        ),
                        "some_dau_impact": ABSOLUTE_METRIC_DATA_F.model_dump(
                            exclude_none=True
                        ),
                        "another_count": ABSOLUTE_METRIC_DATA_F.model_dump(
                            exclude_none=True
                        ),
                        "retained": (
                            DIFFERENCE_METRIC_DATA_DAILY_NEGATIVE_CONTROL.model_dump(
                                exclude_none=True
                            )
                        ),
                        "custom_metric": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                    },
                },
            },
        }

        WEEKLY_DATA = {
            "control": {
                "is_control": True,
                "branch_data": {
                    Group.SEARCH.value: {
                        "search_count": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                    },
                    Group.USAGE.value: {},
                    Group.OTHER.value: {
                        "identity": ABSOLUTE_METRIC_DATA_A.model_dump(exclude_none=True),
                        "some_count": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                        "some_ratio": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                        "some_dau_impact": EMPTY_METRIC_DATA.model_dump(
                            exclude_none=True
                        ),
                        "another_count": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                        "retained": (
                            DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL_VARIANT.model_dump(
                                exclude_none=True
                            )
                        ),
                        "custom_metric": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                    },
                },
            },
            "variant": {
                "is_control": False,
                "branch_data": {
                    Group.SEARCH.value: {
                        "search_count": (
                            DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE_CONTROL.model_dump(
                                exclude_none=True
                            )
                        ),
                    },
                    Group.USAGE.value: {},
                    Group.OTHER.value: {
                        "identity": ABSOLUTE_METRIC_DATA_A.model_dump(exclude_none=True),
                        "some_count": ABSOLUTE_METRIC_DATA_A_COVARIATE.model_dump(
                            exclude_none=True
                        ),
                        "some_ratio": ABSOLUTE_METRIC_DATA_A.model_dump(
                            exclude_none=True
                        ),
                        "some_dau_impact": ABSOLUTE_METRIC_DATA_A.model_dump(
                            exclude_none=True
                        ),
                        "another_count": ABSOLUTE_METRIC_DATA_A.model_dump(
                            exclude_none=True
                        ),
                        "retained": (
                            DIFFERENCE_METRIC_DATA_WEEKLY_NEGATIVE_CONTROL.model_dump(
                                exclude_none=True
                            )
                        ),
                        "custom_metric": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                    },
                },
            },
        }

        OVERALL_DATA = {
            "control": {
                "is_control": True,
                "branch_data": {
                    Group.SEARCH.value: {
                        "search_count": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                    },
                    Group.USAGE.value: {},
                    Group.OTHER.value: {
                        "identity": ABSOLUTE_METRIC_DATA_F_WITH_PERCENT.model_dump(
                            exclude_none=True
                        ),
                        "some_count": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                        "some_ratio": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                        "some_dau_impact": EMPTY_METRIC_DATA.model_dump(
                            exclude_none=True
                        ),
                        "another_count": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                        "default_browser_action": EMPTY_METRIC_DATA.model_dump(
                            exclude_none=True
                        ),
                        "retained": (
                            DIFFERENCE_METRIC_DATA_OVERALL_NEUTRAL_VARIANT.model_dump(
                                exclude_none=True
                            )
                        ),
                        "custom_metric": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                    },
                },
            },
            "variant": {
                "is_control": False,
                "branch_data": {
                    Group.SEARCH.value: {
                        "search_count": (
                            DIFFERENCE_METRIC_DATA_OVERALL_POSITIVE_CONTROL.model_dump(
                                exclude_none=True
                            )
                        ),
                    },
                    Group.USAGE.value: {},
                    Group.OTHER.value: {
                        "identity": ABSOLUTE_METRIC_DATA_F_WITH_PERCENT.model_dump(
                            exclude_none=True
                        ),
                        "some_count": ABSOLUTE_METRIC_DATA_F_COVARIATE.model_dump(
                            exclude_none=True
                        ),
                        "some_ratio": ABSOLUTE_METRIC_DATA_F.model_dump(
                            exclude_none=True
                        ),
                        "some_dau_impact": ABSOLUTE_METRIC_DATA_F.model_dump(
                            exclude_none=True
                        ),
                        "another_count": ABSOLUTE_METRIC_DATA_F.model_dump(
                            exclude_none=True
                        ),
                        "retained": (
                            DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE_CONTROL.model_dump(
                                exclude_none=True
                            )
                        ),
                        "custom_metric": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
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
            FORMATTED_DAILY_DATA,
            OVERALL_DATA,
            WEEKLY_DATA,
            primary_outcomes,
            AnalysisBasis.ENROLLMENTS,
        )
        cls.add_all_outcome_data(
            DAILY_EXPOSURES_DATA,
            FORMATTED_DAILY_DATA,
            OVERALL_DATA,
            WEEKLY_DATA,
            primary_outcomes,
            AnalysisBasis.EXPOSURES,
        )

        return (
            DAILY_DATA,
            FORMATTED_DAILY_DATA,
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

        CONTROL_DATA_ROW = DATA_IDENTITY_ROW.model_copy()
        CONTROL_DATA_ROW.branch = "control"

        VARIANT_DATA_ROW = DATA_IDENTITY_ROW.model_copy()
        VARIANT_DATA_ROW.branch = "variant"

        SEGMENTED_ROW_VARIANT = VARIANT_DATA_ROW.model_copy()
        SEGMENTED_ROW_VARIANT.segment = "some_segment"
        SEGMENTED_ROW_CONTROL = CONTROL_DATA_ROW.model_copy()
        SEGMENTED_ROW_CONTROL.segment = "some_segment"

        VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW = DATA_IDENTITY_ROW.model_copy()
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
        EXPOSURES_CONTROL_DATA_ROW = DATA_IDENTITY_ROW.model_copy()
        EXPOSURES_CONTROL_DATA_ROW.branch = "control"
        EXPOSURES_CONTROL_DATA_ROW.analysis_basis = AnalysisBasis.EXPOSURES

        EXPOSURES_VARIANT_DATA_ROW = DATA_IDENTITY_ROW.model_copy()
        EXPOSURES_VARIANT_DATA_ROW.branch = "variant"
        EXPOSURES_VARIANT_DATA_ROW.analysis_basis = AnalysisBasis.EXPOSURES

        EXPOSURES_SEGMENTED_ROW_VARIANT = VARIANT_DATA_ROW.model_copy()
        EXPOSURES_SEGMENTED_ROW_VARIANT.segment = "some_segment"
        EXPOSURES_SEGMENTED_ROW_VARIANT.analysis_basis = AnalysisBasis.EXPOSURES
        EXPOSURES_SEGMENTED_ROW_CONTROL = CONTROL_DATA_ROW.model_copy()
        EXPOSURES_SEGMENTED_ROW_CONTROL.segment = "some_segment"
        EXPOSURES_SEGMENTED_ROW_CONTROL.analysis_basis = AnalysisBasis.EXPOSURES

        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN = DATA_IDENTITY_ROW.model_copy()
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.metric = "some_count"
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.statistic = Statistic.MEAN
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.branch = "variant"
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.analysis_basis = (
            AnalysisBasis.EXPOSURES
        )

        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL = (
            DATA_IDENTITY_ROW.model_copy()
        )
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.metric = "another_count"
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.statistic = Statistic.BINOMIAL
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.branch = "variant"
        EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.analysis_basis = (
            AnalysisBasis.EXPOSURES
        )

        DAILY_DATA = [
            CONTROL_DATA_ROW.model_dump(exclude_none=True),
            VARIANT_DATA_ROW.model_dump(exclude_none=True),
            VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.model_dump(exclude_none=True),
            VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.model_dump(exclude_none=True),
            CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW.model_dump(exclude_none=True),
        ]
        DAILY_EXPOSURES_DATA = [
            EXPOSURES_CONTROL_DATA_ROW.model_dump(exclude_none=True),
            EXPOSURES_VARIANT_DATA_ROW.model_dump(exclude_none=True),
            EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_MEAN.model_dump(exclude_none=True),
            EXPOSURES_VARIANT_DATA_DEFAULT_METRIC_ROW_BINOMIAL.model_dump(
                exclude_none=True
            ),
        ]
        SEGMENT_DATA = [
            SEGMENTED_ROW_VARIANT.model_dump(exclude_none=True),
            SEGMENTED_ROW_CONTROL.model_dump(exclude_none=True),
        ]
        SEGMENT_EXPOSURES_DATA = [
            EXPOSURES_SEGMENTED_ROW_VARIANT.model_dump(exclude_none=True),
            EXPOSURES_SEGMENTED_ROW_CONTROL.model_dump(exclude_none=True),
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
            _,
            _,
            _,
            _,
        ) = cls.get_data_points()

        (
            DIFFERENCE_METRIC_DATA_DAILY_NEUTRAL_VARIANT,
            DIFFERENCE_METRIC_DATA_DAILY_NEUTRAL_CONTROL,
            DIFFERENCE_METRIC_DATA_DAILY_POSITIVE_VARIANT,
            DIFFERENCE_METRIC_DATA_DAILY_POSITIVE_CONTROL,
            DIFFERENCE_METRIC_DATA_DAILY_NEGATIVE_VARIANT,
            DIFFERENCE_METRIC_DATA_DAILY_NEGATIVE_CONTROL,
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
            DATA_POINT_A,
            DATA_POINT_F,
        )

        PairwiseBranchComparisonData = cls.get_pairwise_branch_comparison_data()
        PairwiseSignificanceData = cls.get_pairwise_significance_data()

        EMPTY_METRIC_DATA = cls.get_pairwise_metric_data()(
            absolute=BranchComparisonData(),
            difference=PairwiseBranchComparisonData(),
            relative_uplift=PairwiseBranchComparisonData(),
            significance=PairwiseSignificanceData(),
        )

        FORMATTED_DAILY_BASE = {
            "control": {
                "is_control": True,
                "branch_data": {
                    Group.SEARCH.value: {
                        "search_count": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                    },
                    Group.USAGE.value: {},
                    Group.OTHER.value: {
                        "identity": ABSOLUTE_METRIC_DATA_F.model_dump(exclude_none=True),
                        "some_count": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                        "another_count": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                        "retained": (
                            DIFFERENCE_METRIC_DATA_DAILY_NEUTRAL_VARIANT.model_dump(
                                exclude_none=True
                            )
                        ),
                    },
                },
            },
            "variant": {
                "is_control": False,
                "branch_data": {
                    Group.SEARCH.value: {
                        "search_count": (
                            DIFFERENCE_METRIC_DATA_DAILY_POSITIVE_CONTROL.model_dump(
                                exclude_none=True
                            )
                        ),
                    },
                    Group.USAGE.value: {},
                    Group.OTHER.value: {
                        "identity": ABSOLUTE_METRIC_DATA_F.model_dump(exclude_none=True),
                        "some_count": ABSOLUTE_METRIC_DATA_F.model_dump(
                            exclude_none=True
                        ),
                        "another_count": ABSOLUTE_METRIC_DATA_F.model_dump(
                            exclude_none=True
                        ),
                        "retained": (
                            DIFFERENCE_METRIC_DATA_DAILY_NEGATIVE_CONTROL.model_dump(
                                exclude_none=True
                            )
                        ),
                    },
                },
            },
        }

        FORMATTED_DAILY_EXPOSURES_DATA = deepcopy(FORMATTED_DAILY_BASE)
        del FORMATTED_DAILY_EXPOSURES_DATA["control"]["branch_data"][Group.OTHER][
            "retained"
        ]
        del FORMATTED_DAILY_EXPOSURES_DATA["variant"]["branch_data"][Group.OTHER][
            "retained"
        ]
        del FORMATTED_DAILY_EXPOSURES_DATA["control"]["branch_data"][Group.SEARCH][
            "search_count"
        ]
        del FORMATTED_DAILY_EXPOSURES_DATA["variant"]["branch_data"][Group.SEARCH][
            "search_count"
        ]

        FORMATTED_DAILY_SEGMENT_DATA = deepcopy(FORMATTED_DAILY_EXPOSURES_DATA)
        del FORMATTED_DAILY_SEGMENT_DATA["control"]["branch_data"][Group.OTHER][
            "another_count"
        ]
        del FORMATTED_DAILY_SEGMENT_DATA["variant"]["branch_data"][Group.OTHER][
            "another_count"
        ]
        del FORMATTED_DAILY_SEGMENT_DATA["control"]["branch_data"][Group.OTHER][
            "some_count"
        ]
        del FORMATTED_DAILY_SEGMENT_DATA["variant"]["branch_data"][Group.OTHER][
            "some_count"
        ]

        FORMATTED_DAILY_ENROLLMENTS_DATA = deepcopy(FORMATTED_DAILY_BASE)
        del FORMATTED_DAILY_ENROLLMENTS_DATA["control"]["branch_data"][Group.OTHER][
            "another_count"
        ]
        del FORMATTED_DAILY_ENROLLMENTS_DATA["variant"]["branch_data"][Group.OTHER][
            "another_count"
        ]
        del FORMATTED_DAILY_ENROLLMENTS_DATA["control"]["branch_data"][Group.OTHER][
            "some_count"
        ]
        del FORMATTED_DAILY_ENROLLMENTS_DATA["variant"]["branch_data"][Group.OTHER][
            "some_count"
        ]

        FORMATTED_DAILY_DATA = {
            "enrollments": {
                "all": FORMATTED_DAILY_ENROLLMENTS_DATA,
                "some_segment": FORMATTED_DAILY_SEGMENT_DATA,
            },
            "exposures": {
                "all": FORMATTED_DAILY_EXPOSURES_DATA,
                "some_segment": FORMATTED_DAILY_SEGMENT_DATA,
            },
        }

        WEEKLY_BASE = {
            "control": {
                "is_control": True,
                "branch_data": {
                    Group.SEARCH.value: {
                        "search_count": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                    },
                    Group.USAGE.value: {},
                    Group.OTHER.value: {
                        "identity": ABSOLUTE_METRIC_DATA_A.model_dump(exclude_none=True),
                        "some_count": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                        "another_count": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                        "retained": (
                            DIFFERENCE_METRIC_DATA_WEEKLY_NEUTRAL_VARIANT.model_dump(
                                exclude_none=True
                            )
                        ),
                    },
                },
            },
            "variant": {
                "is_control": False,
                "branch_data": {
                    Group.SEARCH.value: {
                        "search_count": (
                            DIFFERENCE_METRIC_DATA_WEEKLY_POSITIVE_CONTROL.model_dump(
                                exclude_none=True
                            )
                        ),
                    },
                    Group.USAGE.value: {},
                    Group.OTHER.value: {
                        "identity": ABSOLUTE_METRIC_DATA_A.model_dump(exclude_none=True),
                        "some_count": ABSOLUTE_METRIC_DATA_A.model_dump(
                            exclude_none=True
                        ),
                        "another_count": ABSOLUTE_METRIC_DATA_A.model_dump(
                            exclude_none=True
                        ),
                        "retained": (
                            DIFFERENCE_METRIC_DATA_WEEKLY_NEGATIVE_CONTROL.model_dump(
                                exclude_none=True
                            )
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

        WEEKLY_ENROLLMENTS_DATA = deepcopy(WEEKLY_BASE)
        del WEEKLY_ENROLLMENTS_DATA["control"]["branch_data"][Group.OTHER][
            "another_count"
        ]
        del WEEKLY_ENROLLMENTS_DATA["variant"]["branch_data"][Group.OTHER][
            "another_count"
        ]
        del WEEKLY_ENROLLMENTS_DATA["control"]["branch_data"][Group.OTHER]["some_count"]
        del WEEKLY_ENROLLMENTS_DATA["variant"]["branch_data"][Group.OTHER]["some_count"]

        WEEKLY_DATA = {
            "enrollments": {
                "all": WEEKLY_ENROLLMENTS_DATA,
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
                        "search_count": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                    },
                    Group.USAGE.value: {},
                    Group.OTHER.value: {
                        "identity": ABSOLUTE_METRIC_DATA_F_WITH_PERCENT.model_dump(
                            exclude_none=True
                        ),
                        "some_count": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                        "another_count": EMPTY_METRIC_DATA.model_dump(exclude_none=True),
                        "retained": (
                            DIFFERENCE_METRIC_DATA_OVERALL_NEUTRAL_VARIANT.model_dump(
                                exclude_none=True
                            )
                        ),
                    },
                },
            },
            "variant": {
                "is_control": False,
                "branch_data": {
                    Group.SEARCH.value: {
                        "search_count": (
                            DIFFERENCE_METRIC_DATA_OVERALL_POSITIVE_CONTROL.model_dump(
                                exclude_none=True
                            )
                        ),
                    },
                    Group.USAGE.value: {},
                    Group.OTHER.value: {
                        "identity": ABSOLUTE_METRIC_DATA_F_WITH_PERCENT.model_dump(
                            exclude_none=True
                        ),
                        "some_count": ABSOLUTE_METRIC_DATA_F.model_dump(
                            exclude_none=True
                        ),
                        "another_count": ABSOLUTE_METRIC_DATA_F.model_dump(
                            exclude_none=True
                        ),
                        "retained": (
                            DIFFERENCE_METRIC_DATA_OVERALL_NEGATIVE_CONTROL.model_dump(
                                exclude_none=True
                            )
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

        OVERALL_ENROLLMENTS_DATA = deepcopy(OVERALL_BASE)
        del OVERALL_ENROLLMENTS_DATA["control"]["branch_data"][Group.OTHER][
            "another_count"
        ]
        del OVERALL_ENROLLMENTS_DATA["variant"]["branch_data"][Group.OTHER][
            "another_count"
        ]
        del OVERALL_ENROLLMENTS_DATA["control"]["branch_data"][Group.OTHER]["some_count"]
        del OVERALL_ENROLLMENTS_DATA["variant"]["branch_data"][Group.OTHER]["some_count"]

        OVERALL_DATA = {
            "enrollments": {
                "all": OVERALL_ENROLLMENTS_DATA,
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
            FORMATTED_DAILY_DATA,
            OVERALL_DATA,
            WEEKLY_DATA,
            primary_outcomes,
            AnalysisBasis.ENROLLMENTS,
        )
        cls.add_all_outcome_data(
            DAILY_EXPOSURES_DATA,
            FORMATTED_DAILY_DATA,
            OVERALL_DATA,
            WEEKLY_DATA,
            primary_outcomes,
            AnalysisBasis.EXPOSURES,
        )

        return (
            DAILY_DATA,
            FORMATTED_DAILY_DATA,
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
            VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW.model_copy()
        )
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.point = 0.0
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.upper = 0.0
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.lower = 0.0
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.metric = Metric.RETENTION
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.statistic = Statistic.BINOMIAL

        CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW = (
            VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW.model_copy()
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
        DATA_POINT_F = DATA_POINT_A.model_copy()
        DATA_POINT_F.window_index = None

        DATA_POINT_B = DataPoint(lower=0, point=0, upper=0, window_index=1)
        DATA_POINT_E = DATA_POINT_B.model_copy()
        DATA_POINT_E.window_index = None

        DATA_POINT_C = DataPoint(lower=0, point=0, upper=0, window_index=1)
        DATA_POINT_D = DATA_POINT_C.model_copy()
        DATA_POINT_D.window_index = None

        ABSOLUTE_METRIC_DATA_A = cls.get_absolute_metric_data(DATA_POINT_A)
        ABSOLUTE_METRIC_DATA_F = cls.get_absolute_metric_data(DATA_POINT_F)
        ABSOLUTE_METRIC_DATA_F_WITH_PERCENT = ABSOLUTE_METRIC_DATA_F.model_copy()
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
            ABSOLUTE_METRIC_DATA_A,
            ABSOLUTE_METRIC_DATA_F,
            DATA_POINT_A,
            DATA_POINT_F,
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
        DATA_POINT_A_COVARIATE,
        DATA_POINT_F_COVARIATE,
    ):
        DIFFERENCE_METRIC_DATA_DAILY_NEUTRAL_CONTROL = cls.get_difference_metric_data(
            DATA_POINT_D,
            SignificanceData(daily={}, weekly={}, overall={}),
            comparison_to_branch="control",
        )
        DIFFERENCE_METRIC_DATA_DAILY_POSITIVE_CONTROL = cls.get_difference_metric_data(
            DATA_POINT_F,
            SignificanceData(daily={}, weekly={}, overall={}),
            comparison_to_branch="control",
        )
        DIFFERENCE_METRIC_DATA_DAILY_NEGATIVE_CONTROL = cls.get_difference_metric_data(
            DATA_POINT_D,
            SignificanceData(daily={}, weekly={}, overall={}),
            comparison_to_branch="control",
        )
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
            is_retention=True,
            comparison_to_branch="control",
        )
        DIFFERENCE_METRIC_DATA_DAILY_NEUTRAL_VARIANT = cls.get_difference_metric_data(
            DATA_POINT_E,
            SignificanceData(daily={}, weekly={}, overall={}),
            comparison_to_branch="variant",
        )
        DIFFERENCE_METRIC_DATA_DAILY_POSITIVE_VARIANT = cls.get_difference_metric_data(
            DATA_POINT_F,
            SignificanceData(daily={}, weekly={}, overall={}),
            comparison_to_branch="variant",
        )
        DIFFERENCE_METRIC_DATA_DAILY_NEGATIVE_VARIANT = cls.get_difference_metric_data(
            DATA_POINT_D,
            SignificanceData(daily={}, weekly={}, overall={}),
            comparison_to_branch="variant",
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
            is_retention=True,
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
            DIFFERENCE_METRIC_DATA_DAILY_NEUTRAL_VARIANT,
            DIFFERENCE_METRIC_DATA_DAILY_NEUTRAL_CONTROL,
            DIFFERENCE_METRIC_DATA_DAILY_POSITIVE_VARIANT,
            DIFFERENCE_METRIC_DATA_DAILY_POSITIVE_CONTROL,
            DIFFERENCE_METRIC_DATA_DAILY_NEGATIVE_VARIANT,
            DIFFERENCE_METRIC_DATA_DAILY_NEGATIVE_CONTROL,
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
        cls,
        data,
        formatted_daily_data,
        overall_data,
        weekly_data,
        primary_outcome,
        analysis_basis,
    ):
        primary_metrics = ["default_browser_action"]
        range_data = DataPoint(lower=0, point=0, upper=0)

        for primary_metric in primary_metrics:
            for branch in DEFAULT_TEST_BRANCHES:
                if Group.OTHER not in overall_data[branch]["branch_data"]:
                    overall_data[branch]["branch_data"][Group.OTHER.value] = {}
                if Group.OTHER not in weekly_data[branch]["branch_data"]:
                    weekly_data[branch]["branch_data"][Group.OTHER.value] = {}
                if Group.OTHER not in formatted_daily_data[branch]["branch_data"]:
                    formatted_daily_data[branch]["branch_data"][Group.OTHER.value] = {}

                data_point_overall = range_data.model_copy()
                data_point_overall.count = 0.0
                overall_data[branch]["branch_data"][Group.OTHER.value][primary_metric] = (
                    cls.get_metric_data(data_point_overall)
                )

                data_point_weekly = range_data.model_copy()
                data_point_weekly.window_index = "1"
                weekly_data[branch]["branch_data"][Group.OTHER.value][primary_metric] = (
                    cls.get_metric_data(data_point_weekly)
                )

                data_point_daily = range_data.model_copy()
                formatted_daily_data[branch]["branch_data"][Group.OTHER.value][
                    primary_metric
                ] = cls.get_metric_data(data_point_daily)

                data.append(
                    JetstreamDataPoint(
                        **range_data.model_dump(exclude_none=True),
                        metric=primary_metric,
                        branch=branch,
                        statistic="binomial",
                        window_index="1",
                        segment=Segment.ALL,
                        analysis_basis=analysis_basis,
                    ).model_dump(exclude_none=True)
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
        DATA_POINT_F = DATA_POINT_A.model_copy()
        DATA_POINT_F.window_index = None

        DATA_POINT_B = DataPoint(lower=None, point=None, upper=None, window_index=None)
        DATA_POINT_E = DATA_POINT_B.model_copy()
        DATA_POINT_E.window_index = None

        DATA_POINT_C = DataPoint(lower=None, point=None, upper=None, window_index=None)
        DATA_POINT_D = DATA_POINT_C.model_copy()
        DATA_POINT_D.window_index = None

        ABSOLUTE_METRIC_DATA_A = cls.get_absolute_metric_data(DATA_POINT_A)
        ABSOLUTE_METRIC_DATA_F = cls.get_absolute_metric_data(DATA_POINT_F)
        ABSOLUTE_METRIC_DATA_F_WITH_PERCENT = ABSOLUTE_METRIC_DATA_F.model_copy()
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
            ABSOLUTE_METRIC_DATA_A,
            ABSOLUTE_METRIC_DATA_F,
            DATA_POINT_A,
            DATA_POINT_F,
        )
