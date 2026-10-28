import datetime as dt

from mozilla_nimbus_schemas.highwind import HighwindCellState, HighwindDirection

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
        return (self.analysis.get("metadata") or {}).get("reference_branch")

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
                    # Already a percentage, not a fraction: the job divides before
                    # writing, so these are never multiplied by 100 for display.
                    "relative": comparison.get("relative"),
                    "state": comparison.get("state"),
                    "direction": comparison.get("direction"),
                    "error": comparison.get("error"),
                }
            )
        return cells

    def get_state(self, cells):
        states = {cell["state"] for cell in cells if cell["state"]}
        for state in STATE_PRECEDENCE:
            if state in states:
                return state
        return HighwindCellState.NOT_STARTED

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
                    "cells": cells,
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
