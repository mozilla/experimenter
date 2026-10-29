# The segment the job writes for every enrolled unit. The Highwind page has no segment
# selector, so this is the one whose branch counts the overview shows.
ALL_ENROLLED = "all_enrolled"


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
