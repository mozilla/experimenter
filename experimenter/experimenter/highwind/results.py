import datetime as dt
from enum import Enum

from mozilla_nimbus_schemas.highwind import (
    HighwindCellState,
    HighwindDirection,
    HighwindWindowKind,
)

from experimenter.metrics import NimbusMetrics
from experimenter.nimbus_ui.constants import METRICS_MIN_BOUNDS_WIDTH

# The segment the job writes for every enrolled unit. The Highwind page has no segment
# selector, so this is the one whose branch counts the overview shows.
ALL_ENROLLED = "all_enrolled"

# A window counts as matured once its comparisons settle.
SETTLED_STATES = {HighwindCellState.FORMING, HighwindCellState.CONFIDENT}

# The aggregation a metric declares when it divides one metric by another. Every window
# of a ratio is comparable with the one before it, so a ratio gets a headline where the
# others are read a window at a time.
RATIO_AGGREGATION = "ratio"


class MetricDirection(str, Enum):
    # The schema's directions, plus the one the page derives. A metric whose confident
    # treatments disagree is mixed, which the job never writes because it describes a
    # metric rather than a single comparison.
    POSITIVE = HighwindDirection.POSITIVE.value
    NEGATIVE = HighwindDirection.NEGATIVE.value
    NEUTRAL = HighwindDirection.NEUTRAL.value
    MIXED = "mixed"


# Which state to show for a metric whose cells disagree, most worth acting on first.
STATE_PRECEDENCE = [
    HighwindCellState.ERROR,
    HighwindCellState.CONFIDENT,
    HighwindCellState.FORMING,
    HighwindCellState.INSUFFICIENT_DATA,
    HighwindCellState.NOT_STARTED,
]


def as_fraction(interval):
    if not interval:
        return None
    return {
        key: None if value is None else value / 100 for key, value in interval.items()
    }


def winsorization(window_result):
    # Absent on a window the job has not computed, so there is nothing to report.
    mode = (window_result or {}).get("winsorize_mode")
    if not mode:
        return None
    return {
        "mode": mode,
        "post_threshold": window_result.get("post_winsorize_threshold"),
        "pre_threshold": window_result.get("pre_winsorize_threshold"),
        # Only the branches that lost values to the threshold, which is what says how
        # much the clipping actually did.
        "clipped": [
            {"branch": branch["branch"], "share": branch["clipped_share"]}
            for branch in window_result.get("branches") or []
            if branch.get("clipped_share")
        ],
    }


def parse_date(value):
    # An ISO date string, which the date filter cannot format on its own.
    return dt.date.fromisoformat(value) if value else None


class HighwindResultsManager:
    def __init__(self, experiment):
        self.experiment = experiment
        self.analysis = experiment.analysis_data or {}

    @property
    def has_analysis(self):
        return bool(self.analysis)

    @property
    def reference_branch(self):
        return self.metadata.get("reference_branch")

    @property
    def metadata(self):
        return self.analysis.get("metadata") or {}

    @property
    def errors(self):
        return sorted(
            self.analysis.get("errors") or [],
            key=lambda error: error.get("timestamp") or "",
            reverse=True,
        )

    @property
    def error_count(self):
        return len(self.errors)

    def get_segment(self, slug=ALL_ENROLLED):
        for segment in self.analysis.get("segments") or []:
            if segment.get("slug") == slug:
                return segment
        return None

    def enrolled_counts(self, segment_slug=ALL_ENROLLED):
        segment = self.get_segment(segment_slug) or {}
        return {
            branch["branch"]: branch["units"] for branch in segment.get("branches") or []
        }

    def get_branch_data(self, segment_slug=ALL_ENROLLED):
        counts = self.enrolled_counts(segment_slug)
        total = sum(counts.values())

        # No exposure figures: Highwind analyses enrollments only, and the branch card
        # hides its exposure row unless the view declares an exposure status.
        return [
            {
                "slug": branch.slug,
                "name": branch.name,
                "description": branch.description,
                "screenshots": branch.screenshots.all,
                "num_enrolled_clients": counts.get(branch.slug, 0),
                "percentage": (
                    counts.get(branch.slug, 0) / total * 100 if total else None
                ),
            }
            for branch in self.experiment.get_sorted_branches()
        ]

    def get_segment_result(self, metric, segment_slug=ALL_ENROLLED):
        for segment in metric.get("segments") or []:
            if segment.get("segment") == segment_slug:
                return segment
        return None

    def summarise_window(self, window_result):
        # Every window the job reports carries one, so there is no absent case.
        window = window_result["window"]
        span_days = window["end_day"] - window["start_day"] + 1
        return {
            **window,
            "span_days": span_days,
            # How the stack names each row. A cumulative window always starts at
            # enrolment, so its span says everything; a disjoint one needs both ends.
            "label": (
                f"first {span_days} days"
                if window["kind"] == HighwindWindowKind.CUMULATIVE
                else f"days {window['start_day']}\u2013{window['end_day']}"
            ),
            "matures_on": parse_date(window.get("matures_on")),
        }

    def get_cells(self, window_result):
        # The reference branch has no comparison against itself, so it carries an
        # absolute value and nothing else.
        reference = self.reference_branch
        comparisons = {
            comparison["branch"]: comparison
            for comparison in (window_result or {}).get("comparisons") or []
        }

        cells = []
        for branch in (window_result or {}).get("branches") or []:
            slug = branch["branch"]
            comparison = comparisons.get(slug) or {}
            cells.append(
                {
                    "branch": slug,
                    "is_reference": slug == reference,
                    "n": branch.get("n"),
                    "absolute": branch.get("value"),
                    # The treatment's shift against the reference, which the branch's
                    # own value does not show.
                    "absolute_shift": comparison.get("absolute"),
                    # The blob carries a percentage and the shared cards multiply by
                    # 100, so this hands them the fraction form.
                    "relative": as_fraction(comparison.get("relative")),
                    "state": comparison.get("state"),
                    "direction": comparison.get("direction"),
                    "error": comparison.get("error"),
                }
            )
        return cells

    def relative_extreme(self, cells):
        bounds = [
            bound
            for cell in cells
            if cell["relative"]
            for bound in (cell["relative"]["lower"], cell["relative"]["upper"])
            if bound is not None
        ]
        return max((abs(bound) for bound in bounds), default=None)

    def bar_geometry(self, cells, extreme):
        # The same maths the Jetstream view does for its relative change bar. The scale
        # is passed in rather than taken from these cells, so every window of a metric
        # draws against its widest interval: one that narrows draws a shorter bar
        # instead of being redrawn to fill the same width.
        if extreme is None:
            return {}
        confidence_range = round(extreme * 100 * 1000) / 10
        full_width = confidence_range * 2 if confidence_range else 1

        geometry = {}
        for cell in cells:
            relative = cell["relative"] or {}
            lower, upper = relative.get("lower"), relative.get("upper")
            if lower is None or upper is None:
                continue
            lower, upper = lower * 100, upper * 100
            bar_width = ((upper - lower) / full_width) * 100
            left_percent = (abs(lower + confidence_range) / full_width) * 100
            digits = len(str(round(lower, 1)).replace(".", "")) + len(
                str(round(upper, 1)).replace(".", "")
            )
            left_bounds_percent = left_percent
            if bar_width < METRICS_MIN_BOUNDS_WIDTH:
                left_bounds_percent -= (METRICS_MIN_BOUNDS_WIDTH - bar_width) / 2
            geometry[cell["branch"]] = {
                "bar_width": bar_width,
                "left_percent": left_percent,
                "left_bounds_percent": left_bounds_percent - digits * 1.5,
                "bounds_width": max(bar_width, METRICS_MIN_BOUNDS_WIDTH) + digits * 3,
            }
        return geometry

    def get_precision(self, cells):
        # A rate near zero reads as "0.97 - 0.97" at two decimals, so small values get
        # more of them.
        values = [
            abs(bound)
            for cell in cells
            for interval in (cell["absolute"], cell["absolute_shift"])
            if interval
            for bound in interval.values()
            if bound is not None
        ]
        largest = max(values, default=0)
        if largest >= 100:
            return 1
        if largest >= 1:
            return 2
        return 4

    def get_direction(self, cells):
        # Which way the confident cells moved, so the grid can show one arrow. Treatments
        # that disagree report mixed, which is not the same as no change.
        directions = {
            cell["direction"]
            for cell in cells
            if cell["state"] == HighwindCellState.CONFIDENT
        }
        if len(directions) == 1:
            return MetricDirection(directions.pop())
        if len(directions) > 1:
            return MetricDirection.MIXED
        return MetricDirection.NEUTRAL

    def get_state(self, cells):
        states = {cell["state"] for cell in cells if cell["state"]}
        for state in STATE_PRECEDENCE:
            if state in states:
                return state
        return HighwindCellState.NOT_STARTED

    def get_all_windows(self, metric, segment_slug=ALL_ENROLLED):
        # In the order the job writes them: cumulative first, then disjoint.
        segment = self.get_segment_result(metric, segment_slug) or {}
        windows = []
        for window_result in segment.get("windows") or []:
            cells = self.get_cells(window_result)
            windows.append(
                {
                    **self.summarise_window(window_result),
                    "cells": cells,
                    "state": self.get_state(cells),
                    "precision": self.get_precision(cells),
                    "winsorization": winsorization(window_result),
                }
            )
        return windows

    def has_headline(self, aggregation):
        # A ratio's windows all measure the same thing, so one of them can speak for
        # the metric. Every other shape is read a window at a time. Kept apart from
        # the rule below so another shape can qualify without restating it.
        return aggregation == RATIO_AGGREGATION

    def headline_window(self, windows):
        # Taken from the windows that run from enrolment, so a single week never
        # speaks for the metric: the deepest confident one, or the deepest still
        # forming when none has settled. An errored or starved window answers
        # nothing, so it is never the headline.
        cumulative = [
            window
            for window in windows
            if window["kind"] == HighwindWindowKind.CUMULATIVE
        ]
        for state in (HighwindCellState.CONFIDENT, HighwindCellState.FORMING):
            settled = [window for window in cumulative if window["state"] == state]
            if settled:
                return max(settled, key=lambda window: window["end_day"])
        return None

    def aggregations(self):
        # How each metric is computed, which the blob does not carry. Matched by slug
        # against the application's own catalog.
        catalog = NimbusMetrics.by_application(self.experiment.application)
        return {metric.slug: metric.aggregation for metric in catalog.metrics}

    def get_metrics(self, segment_slug=ALL_ENROLLED):
        aggregations = self.aggregations()
        metrics = []

        for metric in self.analysis.get("metrics") or []:
            slug = metric.get("slug")
            windows = self.get_all_windows(metric, segment_slug)
            cells = [cell for window in windows for cell in window["cells"]]

            extreme = self.relative_extreme(cells)
            precision = self.get_precision(cells)
            for window in windows:
                window["bar_geometry"] = self.bar_geometry(window["cells"], extreme)
                window["precision"] = precision

            has_headline = self.has_headline(aggregations.get(slug))
            metrics.append(
                {
                    "slug": slug,
                    "friendly_name": metric.get("friendly_name") or slug,
                    "description": metric.get("description"),
                    "windows": windows,
                    "precision": precision,
                    "state": self.get_state(cells),
                    "has_headline": has_headline,
                    # Clipping is set on the metric, so every window it applies to
                    # reports the same mode.
                    "winsorization": next(
                        (
                            window["winsorization"]
                            for window in windows
                            if window["winsorization"]
                        ),
                        None,
                    ),
                    "headline": (self.headline_window(windows) if has_headline else None),
                    # A window that has not started renders a row saying so, so a metric
                    # with nothing but those has nothing to draw.
                    "has_results": bool(
                        cells and self.get_state(cells) != HighwindCellState.NOT_STARTED
                    ),
                    # The next window to mature, which is what an unstarted metric waits
                    # on.
                    "matures_on": min(
                        (
                            window["matures_on"]
                            for window in windows
                            if window["state"] == HighwindCellState.NOT_STARTED
                            and window["matures_on"]
                        ),
                        default=None,
                    ),
                    "direction": self.get_direction(cells),
                    "has_confident_change": any(
                        cell["state"] == HighwindCellState.CONFIDENT
                        and cell["direction"] != HighwindDirection.NEUTRAL
                        for cell in cells
                    ),
                }
            )

        return metrics

    def get_notable_metrics(self, segment_slug=ALL_ENROLLED):
        return [
            metric
            for metric in self.get_metrics(segment_slug)
            if metric["has_confident_change"]
        ]
