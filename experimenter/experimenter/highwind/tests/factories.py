import datetime as dt
import json

from django.utils import timezone
from mozilla_nimbus_schemas.highwind import (
    HighwindAnalysis,
    HighwindAnalysisUnit,
    HighwindBranchValue,
    HighwindCellState,
    HighwindComparison,
    HighwindDirection,
    HighwindError,
    HighwindInterval,
    HighwindMetadata,
    HighwindMetricResult,
    HighwindSegment,
    HighwindSegmentBranch,
    HighwindSegmentResult,
    HighwindWindow,
    HighwindWindowKind,
    HighwindWindowResult,
)
from polyfactory.factories.pydantic_factory import ModelFactory

from experimenter.highwind.client import SCHEMA_VERSION
from experimenter.highwind.results import ALL_ENROLLED


class HighwindIntervalFactory(ModelFactory[HighwindInterval]):
    __model__ = HighwindInterval


class HighwindWindowFactory(ModelFactory[HighwindWindow]):
    __model__ = HighwindWindow


class HighwindBranchValueFactory(ModelFactory[HighwindBranchValue]):
    __model__ = HighwindBranchValue


class HighwindComparisonFactory(ModelFactory[HighwindComparison]):
    __model__ = HighwindComparison


class HighwindWindowResultFactory(ModelFactory[HighwindWindowResult]):
    __model__ = HighwindWindowResult


class HighwindSegmentResultFactory(ModelFactory[HighwindSegmentResult]):
    __model__ = HighwindSegmentResult


class HighwindMetricResultFactory(ModelFactory[HighwindMetricResult]):
    __model__ = HighwindMetricResult


class HighwindSegmentBranchFactory(ModelFactory[HighwindSegmentBranch]):
    __model__ = HighwindSegmentBranch


class HighwindSegmentFactory(ModelFactory[HighwindSegment]):
    __model__ = HighwindSegment


class HighwindErrorFactory(ModelFactory[HighwindError]):
    __model__ = HighwindError


class HighwindMetadataFactory(ModelFactory[HighwindMetadata]):
    __model__ = HighwindMetadata

    schema_version = SCHEMA_VERSION
    analysis_unit = HighwindAnalysisUnit.CLIENT_ID
    reference_branch = "control"
    branches = ["control", "treatment"]


class HighwindAnalysisFactory(ModelFactory[HighwindAnalysis]):
    __model__ = HighwindAnalysis


def build_legacy_analysis_json(slug):
    # Carries no schema version, and nothing in it matches the published model.
    return json.dumps(
        {
            "metrics_metadata": {
                "experiment_slug": slug,
                "branches": ["control", "treatment"],
            },
            "statistics": [{"metric": "days_of_use", "branch": "control"}],
            "errors": [],
        }
    )


def build_analysis(slug="test-experiment", generated_at=None, **kwargs):
    # Empty by default, so a test only carries the part it is about. These are passed
    # rather than declared on the factory, since a value declared there wins over the
    # one a caller passes to build().
    return HighwindAnalysisFactory.build(
        metadata=HighwindMetadataFactory.build(
            experiment_slug=slug, generated_at=generated_at or timezone.now()
        ),
        **{"segments": [], "metrics": [], "errors": [], **kwargs},
    )


def build_interval(point=1.0, spread=None):
    # Takes either a point to spread around, or the three bounds spelled out.
    if isinstance(point, dict):
        return HighwindIntervalFactory.build(**point)
    if point is None:
        return HighwindIntervalFactory.build(point=None, lower=None, upper=None)
    if spread is None:
        spread = 0.5
    return HighwindIntervalFactory.build(
        point=point, lower=point - spread, upper=point + spread
    )


def build_window(
    kind=HighwindWindowKind.CUMULATIVE,
    start_day=0,
    end_day=6,
    matures_on="2026-10-08",
    state=HighwindCellState.CONFIDENT,
    direction=HighwindDirection.POSITIVE,
    is_summary=True,
    reference="control",
    treatments=("treatment",),
    value=1.0,
    relative=1.0,
    spread=None,
    error=None,
):
    # One comparison per treatment against the reference, which has none of its own.
    branches = [reference, *treatments]
    return HighwindWindowResultFactory.build(
        window=HighwindWindowFactory.build(
            kind=kind,
            start_day=start_day,
            end_day=end_day,
            matures_on=dt.date.fromisoformat(matures_on) if matures_on else None,
        ),
        is_summary=is_summary,
        branches=[
            HighwindBranchValueFactory.build(
                branch=branch, n=100, value=build_interval(value, spread)
            )
            for branch in branches
        ],
        comparisons=[
            HighwindComparisonFactory.build(
                branch=treatment,
                reference_branch=reference,
                state=state,
                direction=direction,
                relative=build_interval(relative),
                absolute=build_interval(value, spread),
                n_reference=100,
                n_treatment=100,
                error=error,
            )
            for treatment in treatments
        ],
    )


def build_metric(
    slug="days_of_use",
    friendly_name=None,
    description=None,
    windows=None,
    segment=ALL_ENROLLED,
):
    return HighwindMetricResultFactory.build(
        slug=slug,
        friendly_name=friendly_name or slug,
        description=description,
        segments=[
            HighwindSegmentResultFactory.build(
                segment=segment,
                windows=[build_window()] if windows is None else windows,
            )
        ],
    )


def build_analysis_data(slug="test-experiment", **kwargs):
    # The stored form the results manager reads, rather than the model the loader holds.
    return build_analysis(slug=slug, **kwargs).model_dump(mode="json")


def build_segment(
    slug=ALL_ENROLLED, friendly_name="All enrolled", branches=None, units=630465
):
    return HighwindSegmentFactory.build(
        slug=slug,
        friendly_name=friendly_name,
        description=None,
        branches=[
            HighwindSegmentBranchFactory.build(branch=branch, units=units)
            for branch in branches or ["control", "treatment"]
        ],
    )
