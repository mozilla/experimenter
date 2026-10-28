import logging

from django.core.management.base import BaseCommand
from django.utils import timezone
from mozilla_nimbus_schemas.highwind import (
    HighwindCellState,
    HighwindDirection,
    HighwindWindowKind,
)

from experimenter.experiments.models import NimbusExperiment
from experimenter.highwind.tests.factories import (
    build_analysis,
    build_metric,
    build_segment,
    build_window,
)

logger = logging.getLogger()

# One metric per state, so every path on the page has something to show, at magnitudes
# a real blob carries: a count in the thousands, a mean in the tens, a proportion.
METRICS = [
    (
        "days_of_use",
        "Days of use",
        HighwindCellState.FORMING,
        HighwindDirection.NEUTRAL,
        22.606,
        0.14,
    ),
    (
        "uri_count",
        "URIs visited",
        HighwindCellState.CONFIDENT,
        HighwindDirection.NEGATIVE,
        5103.167,
        -2.38,
    ),
    (
        "is_pinned",
        "Is pinned",
        HighwindCellState.CONFIDENT,
        HighwindDirection.POSITIVE,
        0.4696,
        1.25,
    ),
    (
        "qualified_cumulative_days_of_use",
        "QCDOU",
        HighwindCellState.INSUFFICIENT_DATA,
        HighwindDirection.NEUTRAL,
        20.403,
        None,
    ),
    (
        "active_hours",
        "Active hours",
        HighwindCellState.ERROR,
        HighwindDirection.NEUTRAL,
        23.581,
        None,
    ),
]


class Command(BaseCommand):
    help = "Puts dummy Highwind analysis data on live and complete experiments"

    def handle(self, *args, **options):
        experiments = NimbusExperiment.objects.filter(
            status__in=[NimbusExperiment.Status.LIVE, NimbusExperiment.Status.COMPLETE]
        )

        for experiment in experiments:
            # Nothing to compare without a reference branch, or without a treatment.
            if experiment.reference_branch is None:
                continue
            branches = [branch.slug for branch in experiment.get_sorted_branches()]
            reference = experiment.reference_branch.slug
            treatments = [slug for slug in branches if slug != reference]
            if not treatments:
                continue

            experiment.analysis_data = build_analysis(
                slug=experiment.slug,
                segments=[
                    build_segment(branches=branches, units=630465 + 1200 * index)
                    for index in [0]
                ],
                metrics=[
                    build_metric(
                        slug=slug,
                        friendly_name=name,
                        windows=self.windows(
                            reference, treatments, state, direction, value, relative
                        ),
                    )
                    for slug, name, state, direction, value, relative in METRICS
                ],
            ).model_dump(mode="json")
            experiment.analysis_last_updated = timezone.now()
            experiment.save(update_fields=["analysis_data", "analysis_last_updated"])
            logger.info(f"Loaded Highwind results for {experiment.slug}")

    def windows(self, reference, treatments, state, direction, value, relative):
        # Weekly cumulative windows that mature in turn, plus one that has not started,
        # and a disjoint set so the per week breakdown has something in it.
        settled = [
            build_window(
                end_day=end_day,
                matures_on="2026-10-20",
                state=state,
                direction=direction,
                is_summary=end_day == 20,
                reference=reference,
                treatments=treatments,
                value=round(value * (end_day + 1) / 21, 3),
                # An interval proportional to the value, as a real metric's is.
                spread=round(abs(value) * 0.02, 3) or None,
                relative=relative,
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
                matures_on="2026-10-20",
                state=state,
                direction=direction,
                is_summary=False,
                reference=reference,
                treatments=treatments,
                value=round(value / 3, 3),
                spread=round(abs(value) * 0.02, 3) or None,
                relative=relative,
            )
            for start_day in (0, 7, 14)
        ]
        return [*settled, upcoming, *weekly]
