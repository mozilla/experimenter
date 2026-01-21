from collections import defaultdict
from itertools import chain, zip_longest

from experimenter.experiments.constants import (
    NimbusConstants,
)
from experimenter.metrics import MetricAreas
from experimenter.nimbus_ui.constants import NimbusUIConstants
from experimenter.outcomes import Outcomes


class ExperimentResultsManager:
    def __init__(self, experiment):
        self.experiment = experiment

    def get_branch_data(self, analysis_basis, selected_segment, window="overall"):
        window_results = self.get_window_results(analysis_basis, selected_segment, window)

        branch_data = []

        for branch in self.experiment.get_sorted_branches():
            slug = branch.slug
            participant_metrics = (
                window_results.get(slug, {})
                .get("branch_data", {})
                .get("other_metrics", {})
                .get("identity", {})
            )
            num_participants = (
                participant_metrics.get("absolute", {}).get("first", {}).get("point", 0)
            )

            branch_data.append(
                {
                    "slug": slug,
                    "name": branch.name,
                    "screenshots": branch.screenshots.all,
                    "description": branch.description,
                    "percentage": participant_metrics.get("percent"),
                    "num_participants": num_participants,
                },
            )

        return branch_data

    def get_max_metric_value(
        self,
        analysis_basis,
        segment,
        reference_branch,
        outcome_group,
        outcome_slug,
    ):
        overall_results = self.get_window_results(analysis_basis, segment, "overall")
        max_value = 0

        for branch in self.experiment.get_sorted_branches():
            if overall_results:
                for data_point in (
                    overall_results.get(branch.slug, {})
                    .get("branch_data", {})
                    .get(outcome_group, {})
                    .get(outcome_slug, {})
                    .get("relative_uplift", {})
                    .get(reference_branch, {})
                    .get("all", [])
                ):
                    if not data_point:
                        continue

                    lower = data_point.get("lower")
                    upper = data_point.get("upper")

                    max_value = max(max_value, abs(lower), abs(upper))

        return max_value

    def get_weekly_metric_data(self, analysis_basis, segment, reference_branch):
        all_metrics = self.get_metric_data(analysis_basis, segment, reference_branch)

        weekly_metric_data = {}

        for metric_data in all_metrics.values():
            metadata = metric_data.get("metrics", {})

            for metric_metadata in metadata:
                data = (
                    metric_data.get("data", {})
                    .get("weekly", {})
                    .get(metric_metadata["slug"], {})
                )
                weekly_data = {}

                for branch_slug, branch_data in data.items():
                    # Always produce a list of pairs by zipping absolute and relative
                    # When one side is missing or shorter, pad it with None so templates
                    # can iterate without complex conditionals.
                    abs_list = branch_data.get("absolute") or []
                    rel_list = branch_data.get("relative") or []

                    if abs_list or rel_list:
                        weekly_data[branch_slug] = list(
                            zip_longest(abs_list, rel_list, fillvalue=None)
                        )

                if weekly_data:
                    weekly_metric_data[metric_metadata["slug"]] = {
                        "has_weekly_data": True,
                        "data": weekly_data,
                    }
                else:
                    weekly_metric_data[metric_metadata["slug"]] = {
                        "has_weekly_data": False,
                        "data": {},
                    }

        return weekly_metric_data

    def window_index_for_sort(self, point):
        wi = point.get("window_index")
        return int(wi) if wi is not None else 0

    def format_absolute_entries(self, metric_src, significance_map):
        absolute_data_list = metric_src.get("absolute", {}).get("all", [])
        absolute_data_list.sort(key=self.window_index_for_sort)
        abs_entries = []
        for i, data_point in enumerate(absolute_data_list):
            lower = data_point.get("lower")
            upper = data_point.get("upper")
            significance = significance_map.get(str(i + 1), "neutral")
            abs_entries.append(
                {"lower": lower, "upper": upper, "significance": significance}
            )
        return abs_entries

    def format_relative_entries(self, metric_src, significance_map, reference_branch):
        relative_data_list = (
            metric_src.get("relative_uplift", {}).get(reference_branch, {}).get("all", [])
        )
        relative_data_list.sort(key=self.window_index_for_sort)
        rel_entries = []
        for i, data_point in enumerate(relative_data_list):
            if not data_point:
                continue

            lower = data_point.get("lower")
            upper = data_point.get("upper")
            avg_rel_change = (
                abs(data_point.get("point")) if data_point.get("point") else None
            )
            significance = significance_map.get(str(i + 1), "neutral")
            rel_entries.append(
                {
                    "lower": lower,
                    "upper": upper,
                    "significance": significance,
                    "avg_rel_change": avg_rel_change,
                }
            )
        return rel_entries

    def build_branch_metrics(self, group, slug, window_results, reference_branch, window):
        branch_metrics = {}
        for branch in self.experiment.get_sorted_branches():
            branch_results = window_results.get(branch.slug, {}).get("branch_data", {})
            metric_src = branch_results.get(group, {}).get(slug, {})

            significance_map = (
                metric_src.get("significance", {})
                .get(reference_branch, {})
                .get(window, {})
            )

            abs_entries = self.format_absolute_entries(metric_src, significance_map)
            rel_entries = self.format_relative_entries(
                metric_src, significance_map, reference_branch
            )

            branch_metrics[branch.slug] = {
                "absolute": abs_entries,
                "relative": rel_entries,
            }

        return branch_metrics

    def metric_has_errors(self, metric_slug, analysis_basis, segment):
        if self.experiment.results_data:
            for error, details in (
                self.experiment.results_data.get("v3", {}).get("errors", {}).items()
            ):
                if (
                    error == metric_slug
                    and details[0].get("analysis_basis") == analysis_basis
                    and details[0].get("segment") == segment
                ):
                    return True
        return False

    def get_kpi_metrics(
        self, analysis_basis, segment, reference_branch, window="overall"
    ):
        kpi_metrics = NimbusConstants.KPI_METRICS.copy()
        window_results = self.get_window_results(analysis_basis, segment, window)
        other_metrics = (
            (
                window_results.get(reference_branch, {})
                .get("branch_data", {})
                .get("other_metrics", {})
            )
            if isinstance(window_results, dict)
            else {}
        )

        if NimbusConstants.DAILY_ACTIVE_USERS in other_metrics:
            diff_metrics = other_metrics.get(NimbusConstants.DAILY_ACTIVE_USERS, {}).get(
                "difference", {}
            )
            for branch in diff_metrics:
                if len(diff_metrics.get(branch, {}).get("all", [])) > 0:
                    kpi_metrics.append(NimbusConstants.DAU_METRIC.copy())
                    break
        elif NimbusConstants.DAYS_OF_USE in other_metrics:
            if (
                len(
                    other_metrics.get(NimbusConstants.DAYS_OF_USE, {})
                    .get("absolute", {})
                    .get("all", [])
                )
                > 0
            ):
                kpi_metrics.append(NimbusConstants.DOU_METRIC.copy())
        else:
            kpi_metrics.append(NimbusConstants.DAU_METRIC.copy())

        for kpi in kpi_metrics:
            if self.metric_has_errors(kpi["slug"], analysis_basis, segment):
                kpi["has_errors"] = True

        return kpi_metrics

    def get_remaining_metrics_metadata(
        self, exclude_slugs=None, analysis_basis=None, segment=None
    ):
        analysis_data = (
            self.experiment.results_data.get("v3", {})
            if self.experiment.results_data
            else {}
        )
        other_metrics = analysis_data.get("other_metrics", {})
        metadata = analysis_data.get("metadata", {})
        metrics_metadata = metadata.get("metrics", {}) if metadata else {}
        defaults = []

        for group, default_metrics in other_metrics.items():
            for slug, metric_friendly_name in default_metrics.items():
                if exclude_slugs and slug in exclude_slugs:
                    continue
                defaults.append(
                    {
                        "slug": slug,
                        "description": metrics_metadata.get(slug, {}).get(
                            "description", ""
                        ),
                        "group": group,
                        "friendly_name": metric_friendly_name,
                        "has_errors": self.metric_has_errors(
                            slug, analysis_basis, segment
                        ),
                    }
                )

        defaults.sort(key=lambda m: m["friendly_name"])

        return defaults

    def get_metric_areas(
        self, analysis_basis, segment, reference_branch, window="overall"
    ):
        metric_areas = defaultdict(list)
        metric_areas[NimbusUIConstants.NOTABLE_METRIC_AREA] = []
        metric_areas[NimbusUIConstants.KPI_AREA] = self.get_kpi_metrics(
            analysis_basis, segment, reference_branch, window
        )

        metrics_metadata = {}
        if self.experiment.results_data:
            v3 = self.experiment.results_data.get("v3") or {}
            metadata = v3.get("metadata") or {}
            metrics_metadata = metadata.get("metrics") or {}

        all_outcome_metric_slugs = []
        for slug in chain(
            self.experiment.primary_outcomes, self.experiment.secondary_outcomes
        ):
            outcome = Outcomes.get_by_slug_and_application(
                slug, self.experiment.application
            )
            metrics = outcome.metrics if outcome else []
            outcome_metrics = []

            for metric in metrics:
                formatted_metric = {
                    "slug": metric.slug,
                    "description": (
                        metric.description
                        if metric.description
                        else metrics_metadata.get(metric.slug, {}).get("description", "")
                    ),
                    "group": "other_metrics",
                    "friendly_name": (
                        metric.friendly_name
                        if metric.friendly_name
                        else metrics_metadata.get(metric.slug, {}).get(
                            "friendly_name", metric.slug
                        )
                    ),
                    "has_errors": self.metric_has_errors(
                        metric.slug, analysis_basis, segment
                    ),
                }
                if formatted_metric not in outcome_metrics:
                    outcome_metrics.append(formatted_metric)
                    all_outcome_metric_slugs.append(metric.slug)

            outcome_metrics.sort(key=lambda m: m["friendly_name"])
            metric_areas[outcome.friendly_name if outcome else slug] = outcome_metrics

        remaining_metrics = self.get_remaining_metrics_metadata(
            exclude_slugs=all_outcome_metric_slugs
        )
        grouped_metrics = []
        for metric in remaining_metrics:
            area = MetricAreas.get(self.experiment.application, metric["slug"])

            metric_areas[area].append(metric)
            grouped_metrics.append(metric)

        metric_areas[NimbusUIConstants.OTHER_METRICS_AREA] = [
            m for m in remaining_metrics if m not in grouped_metrics
        ]

        window_results = self.get_window_results(analysis_basis, segment, window)

        def is_metric_notable(slug, group):
            for branch_data in window_results.values():
                metric_data = (
                    branch_data.get("branch_data", {}).get(group, {}).get(slug, {})
                )
                for branch_significance in metric_data.get("significance", {}).values():
                    if (
                        "positive" in branch_significance.get(window, {}).values()
                        or "negative" in branch_significance.get(window, {}).values()
                    ):
                        return True
            return False

        for metrics in metric_areas.values():
            for metric in metrics:
                if (
                    is_metric_notable(metric["slug"], metric["group"])
                    and metric not in metric_areas[NimbusUIConstants.NOTABLE_METRIC_AREA]
                ):
                    metric_areas[NimbusUIConstants.NOTABLE_METRIC_AREA].append(metric)

        metric_areas[NimbusUIConstants.NOTABLE_METRIC_AREA].sort(
            key=lambda m: m["friendly_name"]
        )
        return metric_areas

    def get_metric_area_data(self, metrics, analysis_basis, segment, reference_branch):
        def get_window_metric_data(reference_branch, window_results, window):
            window_metric_data = {}

            for metric in metrics:
                slug = metric.get("slug")
                group = metric.get("group")

                branch_metrics = self.build_branch_metrics(
                    group, slug, window_results, reference_branch, window
                )

                window_metric_data[slug] = branch_metrics

            return window_metric_data

        metric_data = {
            "overall": get_window_metric_data(
                reference_branch,
                self.get_window_results(analysis_basis, segment, "overall"),
                "overall",
            ),
            "weekly": get_window_metric_data(
                reference_branch,
                self.get_window_results(analysis_basis, segment, "weekly"),
                "weekly",
            ),
        }

        metric_area_data = {"metrics": metrics, "data": metric_data}

        return metric_area_data

    def get_metric_data(
        self, analysis_basis, segment, reference_branch, window="overall"
    ):
        metric_areas = self.get_metric_areas(
            analysis_basis, segment, reference_branch, window
        )
        metric_data = {}

        for area, metrics in metric_areas.items():
            metric_data[area] = self.get_metric_area_data(
                metrics,
                analysis_basis,
                segment,
                reference_branch,
            )

        return metric_data

    def get_window_results(self, analysis_basis, segment, window="overall"):
        return (
            (
                self.experiment.results_data.get("v3", {})
                .get(window, {})
                .get(analysis_basis, {})
                .get(segment, {})
            )
            if self.experiment.results_data
            else {}
        )
