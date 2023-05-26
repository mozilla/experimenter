import json

import pytest
from pydantic import ValidationError

from mozilla_nimbus_schemas.jetstream import (
    AnalysisBasis,
    AnalysisError,
    AnalysisErrors,
)


class TestAnalysisErrors:
    """
    Test cases for analysis errors schemas:
    - AnalysisError, AnalysisErrors
    """

    def test_empty_fails(self):
        with pytest.raises(ValidationError):
            _ = AnalysisError()
        with pytest.raises(ValidationError):
            _ = AnalysisErrors()

    def test_basic_analysis_error(self):
        ae = AnalysisError(
            analysis_basis=AnalysisBasis.enrollments,
            exception="(<class 'errors.TestException'>, TestException('err')",
            exception_type="EnrollmentNotCompleteException",
            experiment="test-experiment-slug",
            filename="cli.py",
            func_name="execute",
            log_level="ERROR",
            message="test-experiment-slug -> Test error.",
            metric="test-metric",
            segment="test-segment",
            statistic="test-statistic",
            timestamp="2023-05-17T06:42:31+00:00",
        )
        assert ae.segment == "test-segment"
        assert ae.metric == "test-metric"
        assert ae.analysis_basis == "enrollments"
        ae_json = ae.json()
        print(ae_json)
        test_json_str = """{
            "analysis_basis": "enrollments",
            "exception": "(<class 'errors.TestException'>, TestException('err')",
            "exception_type": "EnrollmentNotCompleteException",
            "experiment": "test-experiment-slug",
            "filename": "cli.py",
            "func_name": "execute",
            "log_level": "ERROR",
            "message": "test-experiment-slug -> Test error.",
            "metric": "test-metric",
            "segment": "test-segment",
            "statistic": "test-statistic",
            "timestamp": "2023-05-17T06:42:31+00:00"
        }"""
        assert json.loads(ae_json) == json.loads(test_json_str)

    def test_analysis_errors(self):
        ae0 = AnalysisError(
            analysis_basis=AnalysisBasis.enrollments,
            exception="(<class 'errors.TestException'>, TestException('err')",
            exception_type="EnrollmentNotCompleteException",
            experiment="test-experiment-slug",
            filename="cli.py",
            func_name="execute",
            log_level="ERROR",
            message="test-experiment-slug -> Test error.",
            metric="test-metric",
            segment="test-segment",
            statistic="test-statistic",
            timestamp="2023-05-17T06:42:31+00:00",
        )
        ae1 = AnalysisError(
            analysis_basis=AnalysisBasis.exposures,
            exception="(<class 'errors.TestException'>, TestException('err')",
            exception_type="EnrollmentNotCompleteException",
            experiment="test-experiment-slug",
            filename="cli.py",
            func_name="execute",
            log_level="ERROR",
            message="test-experiment-slug -> Test error.",
            metric="test-metric",
            segment="test-segment",
            statistic="test-statistic",
            timestamp="2023-05-17T06:42:31+00:00",
        )
        ae2 = AnalysisError(
            exception="(<class 'errors.TestException'>, TestException('err')",
            exception_type="EnrollmentNotCompleteException",
            experiment="test-experiment-slug",
            filename="cli.py",
            func_name="execute",
            log_level="ERROR",
            message="test-experiment-slug -> Test error.",
            timestamp="2023-05-17T06:42:31+00:00",
        )

        analysis_errors = AnalysisErrors.parse_obj([ae0, ae1])
        assert type(analysis_errors) == AnalysisErrors
        assert len(analysis_errors.__root__) == 2
        analysis_errors.__root__.append(ae2)
        assert len(analysis_errors.__root__) == 3

    def test_parse_analysis_error(self):
        error_json = """
            {
                "exception": "(<class 'errors.EnrollmentNotCompl",
                "exception_type": "EnrollmentNotCompleteException",
                "experiment": "experiment-test-slug",
                "filename": "cli.py",
                "func_name": "execute",
                "log_level": "ERROR",
                "message": "experiment-test-slug -> Experiment has not finished.",
                "metric": null,
                "segment": null,
                "statistic": null,
                "timestamp": "2023-05-17T06:42:31+00:00"
            }
        """
        analysis_error = AnalysisError.parse_raw(error_json)
        assert analysis_error.metric is None
        assert analysis_error.analysis_basis is None

    def test_parse_analysis_error_fails(self):
        error_json = """
            {
                "exception": "(<class 'errors.EnrollmentNotCompl",
                "exception_type": "EnrollmentNotCompleteException",
                "experiment": "experiment-test-slug",
                "filename": "cli.py",
                "func_name": "execute",
                "log_level": "ERROR",
                "message": null,
                "metric": null,
                "segment": null,
                "statistic": null,
                "timestamp": "2023-05-17T06:42:31+00:00"
            }
        """
        with pytest.raises(ValidationError):
            AnalysisError.parse_raw(error_json)

    def test_parse_analysis_errors(self):
        stats_json = """
            [
                {
                    "exception": "(<class 'errors.EnrollmentNotCompl",
                    "exception_type": "EnrollmentNotCompleteException",
                    "experiment": "experiment-test-slug",
                    "filename": "cli.py",
                    "func_name": "execute",
                    "log_level": "ERROR",
                    "message": "experiment-test-slug -> Experiment has not finished.",
                    "metric": null,
                    "segment": null,
                    "statistic": null,
                    "timestamp": "2023-05-17T06:42:31+00:00"
                },
                {
                    "exception": "(<class 'errors.EnrollmentNotCompl",
                    "exception_type": "EnrollmentNotCompleteException",
                    "experiment": "experiment-test-slug",
                    "filename": "cli.py",
                    "func_name": "execute",
                    "log_level": "ERROR",
                    "message": "experiment-test-slug -> Experiment has not finished.",
                    "metric": null,
                    "segment": null,
                    "statistic": null,
                    "timestamp": "2023-05-17T06:42:31+00:00"
                },
                {
                    "exception": "(<class 'errors.EnrollmentNotCompl",
                    "exception_type": "EnrollmentNotCompleteException",
                    "experiment": "experiment-test-slug",
                    "filename": "cli.py",
                    "func_name": "execute",
                    "log_level": "ERROR",
                    "message": "experiment-test-slug -> Experiment has not finished.",
                    "metric": null,
                    "segment": null,
                    "statistic": null,
                    "timestamp": "2023-05-17T06:42:31+00:00"
                }
            ]
        """
        stats = AnalysisErrors.parse_raw(stats_json)
        assert len(stats.__root__) == 3

    def test_parse_analysis_errors_fails(self):
        # this should fail because AnalysisErrors expects a list
        error_json = """
            {
                "analysis_basis": null,
                "exception": "(<class 'errors.EnrollmentNotComp",
                "exception_type": "EnrollmentNotCompleteException",
                "experiment": "experiment-test-slug",
                "filename": "cli.py",
                "func_name": "execute",
                "log_level": "ERROR",
                "message": "experiment-test-slug -> Experiment has not finished.",
                "metric": null,
                "segment": null,
                "statistic": null,
                "timestamp": "2023-05-17T06:42:31+00:00"
            }
        """
        with pytest.raises(ValidationError):
            AnalysisErrors.parse_raw(error_json)
