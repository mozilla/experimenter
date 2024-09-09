import pytest
from pydantic import ValidationError

from mozilla_nimbus_schemas.jetstream import (
    AnalysisBasis,
    AnalysisError,
    AnalysisErrors,
    AnalysisErrorsFactory,
)

"""
Test cases for analysis errors schemas:
- AnalysisError, AnalysisErrors
"""


def test_analysis_errors():
    ae0 = AnalysisError(
        analysis_basis=AnalysisBasis.ENROLLMENTS,
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
        analysis_basis=AnalysisBasis.EXPOSURES,
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

    analysis_errors = AnalysisErrors.model_validate([ae0, ae1])
    assert type(analysis_errors) is AnalysisErrors
    assert len(analysis_errors.root) == 2
    analysis_errors.root.append(ae2)
    assert len(analysis_errors.root) == 3


def test_parse_analysis_errors():
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
                "source": "jetstream",
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
                "source": "jetstream",
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
                "source": "jetstream",
                "statistic": null,
                "timestamp": "2023-05-17T06:42:31+00:00"
            }
        ]
    """
    stats = AnalysisErrors.model_validate_json(stats_json)
    assert len(stats.root) == 3


def test_parse_analysis_errors_fails():
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
            "source": "jetstream",
            "statistic": null,
            "timestamp": "2023-05-17T06:42:31+00:00"
        }
    """
    with pytest.raises(ValidationError):
        AnalysisErrors.model_validate_json(error_json)


def test_analysis_errors_factory():
    analysis_errors = AnalysisErrorsFactory.build()
    AnalysisErrors.model_validate(analysis_errors)


def test_analysis_errors_invalid():
    analysis_errors_dict = AnalysisErrorsFactory.build().model_dump()
    print(analysis_errors_dict)
    analysis_errors_dict[0]["timestamp"] = "not a date!"
    with pytest.raises(ValidationError):
        AnalysisErrors.model_validate(analysis_errors_dict)
