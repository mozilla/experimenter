import json

from django.utils import timezone
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

from experimenter.highwind.client import SCHEMA_VERSION


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
    # A blob from before the results schema, which the job will not rewrite for an
    # experiment that has ended. Carries no schema version and matches nothing published.
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
