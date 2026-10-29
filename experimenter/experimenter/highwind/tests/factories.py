import datetime as dt
import json
import random
from itertools import chain

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
from experimenter.outcomes import Outcomes


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
    # A treatment's own value moves by the relative change it reports, so the branch
    # figures and the change shown beside them agree.
    def treatment_value():
        if value is None or relative is None:
            return value
        return round(value * (1 + relative / 100), 3)

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
                branch=reference, n=100, value=build_interval(value, spread)
            ),
            *[
                HighwindBranchValueFactory.build(
                    branch=treatment,
                    n=100,
                    value=build_interval(treatment_value(), spread),
                )
                for treatment in treatments
            ],
        ],
        comparisons=[
            HighwindComparisonFactory.build(
                branch=treatment,
                reference_branch=reference,
                state=state,
                direction=direction,
                relative=build_interval(relative),
                # The difference between the branches, which is what the job writes here.
                absolute=build_interval(
                    None
                    if value is None or relative is None
                    else round(treatment_value() - value, 3),
                    spread,
                ),
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
    # The stored form, which is what the results manager reads.
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


def build_random_analysis_data(experiment):
    # Metrics come from the experiment's own outcomes, as build_random_results_data does.
    reference = experiment.reference_branch.slug
    branches = [branch.slug for branch in experiment.get_sorted_branches()]
    treatments = [slug for slug in branches if slug != reference]

    outcome_metrics = []
    for slug in chain(experiment.primary_outcomes, experiment.secondary_outcomes):
        outcome = Outcomes.get_by_slug_and_application(slug, experiment.application)
        outcome_metrics.extend(outcome.metrics if outcome else [])

    # An experiment with no outcomes set would otherwise get an empty page, so fall back
    # to what its application measures.
    if not outcome_metrics:
        for outcome in Outcomes.by_application(experiment.application):
            outcome_metrics.extend(outcome.metrics)

    return build_analysis(
        slug=experiment.slug,
        segments=[build_segment(branches=branches)],
        metrics=[
            build_metric(
                slug=metric.slug,
                friendly_name=metric.friendly_name,
                description=metric.description,
                windows=random_windows(reference, treatments),
            )
            for metric in outcome_metrics
        ],
    ).model_dump(mode="json")


def random_windows(reference, treatments):
    # Weekly cumulative windows that mature in turn, the last of them the summary the
    # grid shows, then one still to come, then a disjoint set for the per week breakdown.
    value = random.uniform(0.5, 5000)
    relative = random.uniform(-5, 5)
    state = random.choice(
        [
            HighwindCellState.FORMING,
            HighwindCellState.CONFIDENT,
            HighwindCellState.INSUFFICIENT_DATA,
            HighwindCellState.ERROR,
        ]
    )
    direction = (
        random.choice([HighwindDirection.POSITIVE, HighwindDirection.NEGATIVE])
        if state == HighwindCellState.CONFIDENT
        else HighwindDirection.NEUTRAL
    )
    spread = abs(value) * 0.02

    matured = [
        build_window(
            end_day=end_day,
            state=state,
            direction=direction,
            is_summary=end_day == 20,
            reference=reference,
            treatments=treatments,
            value=round(value * (end_day + 1) / 21, 3),
            spread=round(spread, 3) or None,
            relative=round(relative, 2),
            error="zero variance in reference branch"
            if state == HighwindCellState.ERROR
            else None,
        )
        for end_day in (6, 13, 20)
    ]
    upcoming = build_window(
        end_day=27,
        matures_on="2026-12-01",
        state=HighwindCellState.NOT_STARTED,
        is_summary=False,
        reference=reference,
        treatments=treatments,
        value=None,
        relative=None,
    )
    weekly = [
        build_window(
            kind=HighwindWindowKind.DISJOINT,
            start_day=start_day,
            end_day=start_day + 6,
            state=state,
            direction=direction,
            is_summary=False,
            reference=reference,
            treatments=treatments,
            value=round(value / 3, 3),
            spread=round(spread, 3) or None,
            relative=round(relative, 2),
        )
        for start_day in (0, 7, 14)
    ]
    return [*matured, upcoming, *weekly]
