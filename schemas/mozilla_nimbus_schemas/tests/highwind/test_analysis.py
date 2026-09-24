import copy
import datetime as dt

import pytest
from pydantic import ValidationError

from mozilla_nimbus_schemas.highwind import (
    HighwindAnalysis,
    HighwindAnalysisUnit,
    HighwindCellState,
    HighwindDirection,
    HighwindInterval,
    HighwindLogLevel,
    HighwindWindowKind,
)

NULL_INTERVAL = {"point": None, "lower": None, "upper": None}

WINDOW_CUMULATIVE = {
    "kind": "cumulative",
    "start_day": 0,
    "end_day": 6,
    "matures_on": "2026-01-08",
}

WINDOW_NOT_STARTED = {
    "kind": "cumulative",
    "start_day": 0,
    "end_day": 13,
    "matures_on": None,
}

WINDOW_DISJOINT = {
    "kind": "disjoint",
    "start_day": 7,
    "end_day": 13,
    "matures_on": "2026-01-15",
}

EXAMPLE_ANALYSIS = {
    "metadata": {
        "schema_version": 1,
        "experiment_slug": "test-experiment-slug",
        "as_of_date": "2026-01-10",
        "generated_at": "2026-01-10T06:00:00+00:00",
        "pipeline_version": "0.1.0",
        "start_date": "2026-01-01",
        "end_date": None,
        "analysis_unit": "client_id",
        "reference_branch": "control",
        "branches": ["control", "treatment"],
    },
    "segments": [
        {
            "slug": "test-segment",
            "friendly_name": "Test segment",
            "description": "A test segment.",
            "branches": [
                {"branch": "control", "units": 100},
                {"branch": "treatment", "units": 100},
            ],
        }
    ],
    "metrics": [
        {
            "slug": "test-metric",
            "friendly_name": "Test metric",
            "description": "A test metric.",
            "segments": [
                {
                    "segment": "test-segment",
                    "windows": [
                        {
                            "window": WINDOW_CUMULATIVE,
                            "is_summary": True,
                            "branches": [
                                {
                                    "branch": "control",
                                    "n": 100,
                                    "value": {
                                        "point": 0.5,
                                        "lower": 0.4,
                                        "upper": 0.6,
                                    },
                                },
                                {
                                    "branch": "treatment",
                                    "n": 100,
                                    "value": {
                                        "point": 0.6,
                                        "lower": 0.5,
                                        "upper": 0.7,
                                    },
                                },
                            ],
                            "comparisons": [
                                {
                                    "branch": "treatment",
                                    "reference_branch": "control",
                                    "state": "confident",
                                    "direction": "positive",
                                    "relative": {
                                        "point": 10.0,
                                        "lower": 1.0,
                                        "upper": 20.0,
                                    },
                                    "absolute": {
                                        "point": 0.1,
                                        "lower": 0.01,
                                        "upper": 0.2,
                                    },
                                    "n_reference": 100,
                                    "n_treatment": 100,
                                    "error": None,
                                }
                            ],
                        },
                        {
                            "window": WINDOW_NOT_STARTED,
                            "is_summary": False,
                            "branches": [
                                {
                                    "branch": "control",
                                    "n": 0,
                                    "value": {
                                        "point": None,
                                        "lower": None,
                                        "upper": None,
                                    },
                                },
                                {
                                    "branch": "treatment",
                                    "n": 0,
                                    "value": {
                                        "point": None,
                                        "lower": None,
                                        "upper": None,
                                    },
                                },
                            ],
                            "comparisons": [
                                {
                                    "branch": "treatment",
                                    "reference_branch": "control",
                                    "state": "not_started",
                                    "direction": "neutral",
                                    "relative": NULL_INTERVAL,
                                    "absolute": NULL_INTERVAL,
                                    "n_reference": None,
                                    "n_treatment": None,
                                    "error": None,
                                }
                            ],
                        },
                        {
                            "window": WINDOW_DISJOINT,
                            "is_summary": False,
                            "branches": [
                                {
                                    "branch": "control",
                                    "n": 0,
                                    "value": {
                                        "point": None,
                                        "lower": None,
                                        "upper": None,
                                    },
                                },
                                {
                                    "branch": "treatment",
                                    "n": 0,
                                    "value": {
                                        "point": None,
                                        "lower": None,
                                        "upper": None,
                                    },
                                },
                            ],
                            "comparisons": [
                                {
                                    "branch": "treatment",
                                    "reference_branch": "control",
                                    "state": "error",
                                    "direction": "neutral",
                                    "relative": NULL_INTERVAL,
                                    "absolute": NULL_INTERVAL,
                                    "n_reference": None,
                                    "n_treatment": None,
                                    "error": "Test error.",
                                }
                            ],
                        },
                    ],
                }
            ],
        }
    ],
    "errors": [
        {
            "timestamp": "2026-01-10T06:00:00+00:00",
            "log_level": "ERROR",
            "message": "Test error.",
            "exception_type": "TestException",
            "exception": "Traceback (most recent call last): TestException('err')",
            "filename": "analysis.py",
            "func_name": "run",
            "metric": "test-metric",
            "segment": "test-segment",
            "window": WINDOW_DISJOINT,
        },
        {
            "timestamp": "2026-01-10T06:00:00+00:00",
            "log_level": "WARNING",
            "message": "Test warning.",
            "exception_type": None,
            "exception": None,
            "filename": "cli.py",
            "func_name": "execute",
            "metric": None,
            "segment": None,
            "window": None,
        },
    ],
}


def test_highwind_analysis_validates_example():
    analysis = HighwindAnalysis.model_validate(EXAMPLE_ANALYSIS)

    assert analysis.metadata.as_of_date == dt.date(2026, 1, 10)
    assert analysis.metadata.end_date is None
    assert analysis.metadata.analysis_unit == HighwindAnalysisUnit.CLIENT_ID

    windows = analysis.metrics[0].segments[0].windows
    assert [w.window.kind for w in windows] == [
        HighwindWindowKind.CUMULATIVE,
        HighwindWindowKind.CUMULATIVE,
        HighwindWindowKind.DISJOINT,
    ]
    assert windows[0].window.matures_on == dt.date(2026, 1, 8)
    assert windows[1].window.matures_on is None
    assert windows[0].comparisons[0].state == HighwindCellState.CONFIDENT
    assert windows[0].comparisons[0].direction == HighwindDirection.POSITIVE
    assert windows[1].comparisons[0].state == HighwindCellState.NOT_STARTED
    assert windows[2].comparisons[0].state == HighwindCellState.ERROR

    summary = windows[0]
    assert summary.branches[1].value.point == 0.6
    assert summary.branches[1].value.lower == 0.5
    assert summary.branches[1].value.upper == 0.7
    assert summary.comparisons[0].relative.point == 10.0
    assert summary.comparisons[0].relative.lower == 1.0
    assert summary.comparisons[0].relative.upper == 20.0
    assert summary.comparisons[0].absolute.point == 0.1
    assert summary.comparisons[0].absolute.lower == 0.01
    assert summary.comparisons[0].absolute.upper == 0.2

    assert analysis.errors[0].log_level == HighwindLogLevel.ERROR
    assert analysis.errors[1].window is None


def test_highwind_analysis_round_trips():
    analysis = HighwindAnalysis.model_validate(EXAMPLE_ANALYSIS)
    dumped = analysis.model_dump(mode="json")

    assert HighwindAnalysis.model_validate(dumped) == analysis


def test_highwind_analysis_not_started_intervals_are_null():
    analysis = HighwindAnalysis.model_validate(EXAMPLE_ANALYSIS)
    not_started = analysis.metrics[0].segments[0].windows[1]
    comparison = not_started.comparisons[0]
    null_interval = HighwindInterval(point=None, lower=None, upper=None)

    assert comparison.state == HighwindCellState.NOT_STARTED
    assert comparison.relative == null_interval
    assert comparison.absolute == null_interval
    assert [b.value for b in not_started.branches] == [null_interval, null_interval]


def test_highwind_analysis_optional_descriptions():
    data = copy.deepcopy(EXAMPLE_ANALYSIS)
    del data["segments"][0]["description"]
    del data["metrics"][0]["description"]

    analysis = HighwindAnalysis.model_validate(data)

    assert analysis.segments[0].description is None
    assert analysis.metrics[0].description is None


@pytest.mark.parametrize(
    "path",
    [
        (),
        ("metadata",),
        ("segments", 0),
        ("segments", 0, "branches", 0),
        ("metrics", 0),
        ("metrics", 0, "segments", 0),
        ("metrics", 0, "segments", 0, "windows", 0),
        ("metrics", 0, "segments", 0, "windows", 0, "window"),
        ("metrics", 0, "segments", 0, "windows", 0, "branches", 0),
        ("metrics", 0, "segments", 0, "windows", 0, "branches", 0, "value"),
        ("metrics", 0, "segments", 0, "windows", 0, "comparisons", 0),
        ("metrics", 0, "segments", 0, "windows", 0, "comparisons", 0, "relative"),
        ("metrics", 0, "segments", 0, "windows", 0, "comparisons", 0, "absolute"),
        ("errors", 0),
    ],
)
def test_highwind_analysis_rejects_extra_fields(path):
    data = copy.deepcopy(EXAMPLE_ANALYSIS)
    target = data
    for key in path:
        target = target[key]
    target["unexpected_field"] = "value"

    with pytest.raises(ValidationError, match="unexpected_field"):
        HighwindAnalysis.model_validate(data)


@pytest.mark.parametrize(
    "path,key,value",
    [
        (("metadata",), "analysis_unit", "unknown_unit"),
        (("metrics", 0, "segments", 0, "windows", 0, "window"), "kind", "rolling"),
        (
            ("metrics", 0, "segments", 0, "windows", 0, "comparisons", 0),
            "state",
            "unknown_state",
        ),
        (
            ("metrics", 0, "segments", 0, "windows", 0, "comparisons", 0),
            "direction",
            "sideways",
        ),
        (("errors", 0), "log_level", "INFO"),
    ],
)
def test_highwind_analysis_rejects_unknown_enum_values(path, key, value):
    data = copy.deepcopy(EXAMPLE_ANALYSIS)
    target = data
    for step in path:
        target = target[step]
    target[key] = value

    with pytest.raises(ValidationError):
        HighwindAnalysis.model_validate(data)


@pytest.mark.parametrize(
    "path,key",
    [
        (("metadata",), "end_date"),
        (("metrics", 0, "segments", 0, "windows", 0, "window"), "matures_on"),
        (("metrics", 0, "segments", 0, "windows", 0, "comparisons", 0), "error"),
        (
            ("metrics", 0, "segments", 0, "windows", 0, "comparisons", 0, "relative"),
            "point",
        ),
        (
            ("metrics", 0, "segments", 0, "windows", 0, "comparisons", 0, "absolute"),
            "lower",
        ),
        (("metrics", 0, "segments", 0, "windows", 0, "branches", 0, "value"), "upper"),
        (("errors", 0), "window"),
    ],
)
def test_highwind_analysis_requires_nullable_fields(path, key):
    data = copy.deepcopy(EXAMPLE_ANALYSIS)
    target = data
    for step in path:
        target = target[step]
    del target[key]

    with pytest.raises(ValidationError):
        HighwindAnalysis.model_validate(data)
