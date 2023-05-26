import json

import pytest
from pydantic import ValidationError

from mozilla_nimbus_schemas.jetstream import AnalysisBasis, Statistic, Statistics


class TestStatistics:
    """
    Test cases for statistics schemas:
    - Statistic, Statistics
    """

    def test_empty_statistic_fails(self):
        with pytest.raises(ValidationError):
            _ = Statistic()
        with pytest.raises(ValidationError):
            _ = Statistics()

    def test_basic_statistic(self):
        s = Statistic(
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
        assert s.segment == "all"
        assert s.metric == "test-metric"
        assert s.analysis_basis == "enrollments"
        s_json = s.json()
        test_json_str = """{
            "metric": "test-metric",
            "statistic": "test-statistic",
            "branch": "test-branch",
            "comparison": null,
            "comparison_to_branch": null,
            "ci_width": 0.95,
            "point": 1.0,
            "lower": 0.2,
            "upper": 1.2,
            "segment": "all",
            "analysis_basis": "enrollments",
            "window_index": "1"
        }"""
        assert json.loads(s_json) == json.loads(test_json_str)

    def test_statistics(self):
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

    def test_parse_statistic(self):
        stat_json = """
            {
                "metric": "identity",
                "statistic": "count",
                "branch": "control",
                "point": 0,
                "segment": "all",
                "analysis_basis": "exposures",
                "window_index": "21"
            }
        """
        stat = Statistic.parse_raw(stat_json)
        assert stat.metric == "identity"
        assert stat.analysis_basis == AnalysisBasis.exposures

    def test_parse_statistic_fails(self):
        stat_json = """
            {
                "metric": "identity",
                "statistic": "count",
                "branch": "control",
                "ci_width": 1.2,
                "point": 0,
                "segment": "all",
                "analysis_basis": "exposures",
                "window_index": "21"
            }
        """
        with pytest.raises(ValidationError):
            Statistic.parse_raw(stat_json)

    def test_parse_statistics(self):
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
