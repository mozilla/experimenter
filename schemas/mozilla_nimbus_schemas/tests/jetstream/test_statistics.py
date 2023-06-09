from mozilla_nimbus_schemas.jetstream import AnalysisBasis, Statistic, Statistics

"""
Test cases for statistics schemas:
- Statistic, Statistics
"""


def test_statistics():
    s0 = Statistic(
        metric="test-metric",
        statistic="test-statistic",
        branch="test-branch",
        ci_width=0.95,
        point=1.0,
        lower=0.2,
        upper=1.2,
        analysis_basis=AnalysisBasis.enrollments,
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
        analysis_basis=AnalysisBasis.enrollments,
        window_index="1",
    )
    s2 = Statistic(
        metric="test-metric",
        statistic="test-statistic",
        branch="test-branch",
        ci_width=0.95,
        point=1.0,
        lower=0.2,
        upper=1.2,
        analysis_basis=AnalysisBasis.enrollments,
        window_index="1",
    )

    stats = Statistics.parse_obj([s0, s1])
    assert type(stats) == Statistics
    assert len(stats.__root__) == 2
    stats.__root__.append(s2)
    assert len(stats.__root__) == 3


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
                "segment": "all",
                "analysis_basis": "enrollments",
                "window_index": "8"
            }
        ]
    """
    stats = Statistics.parse_raw(stats_json)
    assert len(stats.__root__) == 3
