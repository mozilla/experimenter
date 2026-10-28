import datetime as dt

from mozilla_nimbus_schemas.highwind import HighwindCellState, HighwindDirection

from experimenter.nimbus_ui.constants import METRICS_MIN_BOUNDS_WIDTH

# The segment the job writes for every enrolled unit. The Highwind page has no segment
# selector, so this is the one whose branch counts the overview shows.
ALL_ENROLLED = "all_enrolled"

# A window counts as matured once its comparisons settle, which is also what the job uses
# to decide which window to mark as the summary.
SETTLED_STATES = {HighwindCellState.FORMING, HighwindCellState.CONFIDENT}

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


def parse_date(value):
    # Stored as an ISO date string, which the date filter cannot format on its own. The
    # schema types the field as a date, so a stored blob never carries anything else.
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

    def get_summary_window(self, metric, segment_slug=ALL_ENROLLED):
        # The job marks this: the largest settled cumulative window, or the latest
        # settled one for a metric declaring only disjoint windows. Reading the flag keeps
        # that rule in the job rather than restating it here, where it could drift.
        segment = self.get_segment_result(metric, segment_slug) or {}
        for window in segment.get("windows") or []:
            if window.get("is_summary"):
                return window
        return None

    def summarise_window(self, window_result):
        window = (window_result or {}).get("window")
        if not window:
            return None
        return {
            **window,
            # The template shows the span where the Jetstream page shows its OVERALL tag.
            "span_days": window["end_day"] - window["start_day"] + 1,
            "matures_on": parse_date(window.get("matures_on")),
        }

    def get_cells(self, window_result):
        # One cell per branch, each carrying its own state so the grid and the modal can
        # render the same thing. The reference branch has no comparison against itself,
        # so it shows an absolute value and nothing else.
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
                    # The blob carries a percentage, but common/metric_card.html runs
                    # these through to_percentage, which multiplies by 100. Converting
                    # here keeps the shared card usable without a Highwind special case.
                    "relative": as_fraction(comparison.get("relative")),
                    "state": comparison.get("state"),
                    "direction": comparison.get("direction"),
                    "error": comparison.get("error"),
                }
            )
        return cells

    def bar_geometry(self, cells):
        # The same maths the Jetstream view does for its relative change bar, scaled
        # against the widest interval on this metric so the bars are comparable.
        bounds = [
            bound
            for cell in cells
            if cell["relative"]
            for bound in (cell["relative"]["lower"], cell["relative"]["upper"])
            if bound is not None
        ]
        if not bounds:
            return {}

        extreme = max(abs(bound) for bound in bounds)
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

    def get_state(self, cells):
        states = {cell["state"] for cell in cells if cell["state"]}
        for state in STATE_PRECEDENCE:
            if state in states:
                return state
        return HighwindCellState.NOT_STARTED

    def get_all_windows(self, metric, segment_slug=ALL_ENROLLED):
        # Every window the run reported, for the per-metric breakdown. Cumulative first,
        # then disjoint, which is the order the job writes them in.
        segment = self.get_segment_result(metric, segment_slug) or {}
        windows = []
        for window_result in segment.get("windows") or []:
            cells = self.get_cells(window_result)
            windows.append(
                {
                    **self.summarise_window(window_result),
                    "cells": cells,
                    "state": self.get_state(cells),
                    "is_summary": window_result.get("is_summary", False),
                }
            )
        return windows

    def get_metrics(self, segment_slug=ALL_ENROLLED):
        metrics = []

        for metric in self.analysis.get("metrics") or []:
            window_result = self.get_summary_window(metric, segment_slug)
            window = self.summarise_window(window_result)
            cells = self.get_cells(window_result)
            states = {cell["state"] for cell in cells}

            metrics.append(
                {
                    "slug": metric.get("slug"),
                    "friendly_name": metric.get("friendly_name") or metric.get("slug"),
                    "description": metric.get("description"),
                    "window": window,
                    "windows": self.get_all_windows(metric, segment_slug),
                    "cells": cells,
                    "bar_geometry": self.bar_geometry(cells),
                    "state": self.get_state(cells),
                    "is_matured": bool(states & SETTLED_STATES),
                    # An errored or insufficient cell is a matured window with no number,
                    # so it still renders a row saying so. Only a window that has not
                    # started has nothing to show at all.
                    "has_results": bool(
                        cells and self.get_state(cells) != HighwindCellState.NOT_STARTED
                    ),
                    # The job falls back to the first window when nothing has settled, so
                    # this is the date an unmatured metric is waiting on.
                    "matures_on": (window or {}).get("matures_on"),
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
