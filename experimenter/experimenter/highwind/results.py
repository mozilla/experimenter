from mozilla_nimbus_schemas.highwind import HighwindCellState, HighwindDirection

# The segment the job writes for every enrolled unit. The Highwind page has no segment
# selector, so this is the one whose branch counts the overview shows.
ALL_ENROLLED = "all_enrolled"

# A window counts as matured once its comparisons settle, which is also what the job uses
# to decide which window to mark as the summary.
SETTLED_STATES = {HighwindCellState.FORMING, HighwindCellState.CONFIDENT}


class HighwindResultsManager:
    def __init__(self, experiment):
        self.experiment = experiment
        self.analysis = experiment.analysis_data or {}

    @property
    def has_analysis(self):
        return bool(self.analysis)

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
        # The job picks this and marks it: the largest settled cumulative window, or the
        # latest settled one for a metric declaring only disjoint windows. Reading the flag
        # keeps that rule in the job rather than restating it here, where it could drift.
        segment = self.get_segment_result(metric, segment_slug) or {}
        for window in segment.get("windows") or []:
            if window.get("is_summary"):
                return window
        return None

    def summarise_window(self, window_result):
        window = (window_result or {}).get("window")
        if not window:
            return None
        # The template shows the span where the Jetstream page shows its OVERALL tag.
        return {**window, "span_days": window["end_day"] - window["start_day"] + 1}

    def get_metrics(self, segment_slug=ALL_ENROLLED):
        metrics = []

        for metric in self.analysis.get("metrics") or []:
            window = self.get_summary_window(metric, segment_slug)
            comparisons = (window or {}).get("comparisons") or []
            states = {comparison.get("state") for comparison in comparisons}

            metrics.append(
                {
                    "slug": metric.get("slug"),
                    "friendly_name": metric.get("friendly_name") or metric.get("slug"),
                    "description": metric.get("description"),
                    "window": self.summarise_window(window),
                    "branches": (window or {}).get("branches") or [],
                    "comparisons": comparisons,
                    "is_matured": bool(states & SETTLED_STATES),
                    "has_confident_change": any(
                        comparison.get("state") == HighwindCellState.CONFIDENT
                        and comparison.get("direction") != HighwindDirection.NEUTRAL
                        for comparison in comparisons
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
