from mozilla_nimbus_schemas.highwind import (
    HighwindAnalysis,
    HighwindAnalysisUnit,
    HighwindBranchValue,
    HighwindComparison,
    HighwindError,
    HighwindInterval,
    HighwindMetadata,
    HighwindMetricResult,
    HighwindSegment,
    HighwindSegmentBranch,
    HighwindSegmentResult,
    HighwindWindow,
    HighwindWindowResult,
)
from polyfactory.factories.pydantic_factory import ModelFactory


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

    schema_version = 1
    analysis_unit = HighwindAnalysisUnit.CLIENT_ID
    reference_branch = "control"
    branches = ["control", "treatment"]


class HighwindAnalysisFactory(ModelFactory[HighwindAnalysis]):
    """A run that produced no results, which is what a test wants unless it says so.

    The pieces a filled-in analysis is built from each have a factory above, so a test
    that needs results passes them in rather than writing the shape out by hand.
    """

    __model__ = HighwindAnalysis

    metadata = HighwindMetadataFactory
    segments = []
    metrics = []
    errors = []


def build_analysis(slug, generated_at, **kwargs):
    """The analysis one experiment's run published, keyed to that experiment."""
    return HighwindAnalysisFactory.build(
        metadata=HighwindMetadataFactory.build(
            experiment_slug=slug, generated_at=generated_at
        ),
        **kwargs,
    )
