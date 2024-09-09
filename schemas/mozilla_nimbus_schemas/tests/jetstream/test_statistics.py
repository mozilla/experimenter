import pytest
from pydantic import ValidationError

from mozilla_nimbus_schemas.jetstream import (
    AnalysisBasis,
    Statistic,
    Statistics,
    StatisticsFactory,
)

"""
Test cases for statistics schemas:
- Statistic, Statistics
"""


def test_statistics():
    s0 = Statistic(
        metric="test-metric",
        statistic="test-statistic",
        branch="test-control",
        ci_width=0.95,
        point=1.0,
        lower=0.2,
        upper=1.2,
        p_value=0.03,
        analysis_basis=AnalysisBasis.ENROLLMENTS,
        window_index="1",
    )
    s1 = Statistic(
        metric="test-metric",
        statistic="test-statistic",
        branch="test-branch",
        ci_width=0.95,
        point=1.0,
        lower=0.2,
        upper=1.2,
        p_value=0.03,
        analysis_basis=AnalysisBasis.ENROLLMENTS,
        window_index="1",
    )
    s2 = Statistic(
        metric="test-metric",
        statistic="test-statistic-2",
        branch="test-branch",
        ci_width=0.95,
        point=1.0,
        lower=0.2,
        upper=1.2,
        p_value=0.03,
        analysis_basis=AnalysisBasis.ENROLLMENTS,
        window_index="1",
    )

    stats = Statistics.model_validate([s0, s1])
    assert type(stats) is Statistics
    assert len(stats.root) == 2
    stats.root.append(s2)
    assert len(stats.root) == 3


def test_parse_statistics():
    stats_json = """
        [
            {
                "metric": "identity",
                "statistic": "count",
                "branch": "control",
                "point": 0,
                "segment": "all",
                "analysis_basis": "exposures",
                "window_index": "21"
            },
            {
                "metric": "retained",
                "statistic": "binomial",
                "branch": "control",
                "ci_width": 0.95,
                "point": 0.4,
                "lower": 0.3,
                "upper": 0.5,
                "p_value": 0.001,
                "segment": "all",
                "analysis_basis": "enrollments",
                "window_index": "2"
            },
            {
                "metric": "unenroll",
                "statistic": "binomial",
                "branch": "treatment-a",
                "comparison": "relative_uplift",
                "comparison_to_branch": "control",
                "ci_width": 0.95,
                "point": 40.5,
                "lower": -0.9,
                "upper": 33,
                "p_value": 0.051,
                "segment": "all",
                "analysis_basis": "enrollments",
                "window_index": "8"
            }
        ]
    """
    stats = Statistics.model_validate_json(stats_json)
    assert len(stats.root) == 3


def test_statistics_factory():
    stats = StatisticsFactory.build()
    Statistics.model_validate(stats)


def test_statistics_invalid():
    stats_dict = StatisticsFactory.build().model_dump()
    stats_dict[0]["ci_width"] = "invalid data"
    with pytest.raises(ValidationError):
        Statistics.model_validate(stats_dict)
