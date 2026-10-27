from django.test import TestCase
from mozilla_nimbus_schemas.highwind import HighwindCellState, HighwindDirection

from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.highwind.results import HighwindResultsManager


def window(kind, start_day, end_day, state, is_summary, direction="neutral"):
    return {
        "window": {
            "kind": kind,
            "start_day": start_day,
            "end_day": end_day,
            "matures_on": "2026-10-08",
        },
        "is_summary": is_summary,
        "branches": [{"branch": "control", "n": 100, "value": {}}],
        "comparisons": [
            {
                "branch": "treatment",
                "reference_branch": "control",
                "state": state,
                "direction": direction,
                "relative": {},
                "absolute": {},
                "n_reference": 100,
                "n_treatment": 100,
                "error": None,
            }
        ],
    }


def metric(slug, windows, friendly_name=None):
    return {
        "slug": slug,
        "friendly_name": friendly_name or slug,
        "description": None,
        "segments": [{"segment": "all_enrolled", "windows": windows}],
    }


class TestHighwindResultsManager(TestCase):
    def manager(self, metrics):
        experiment = NimbusExperimentFactory.create()
        experiment.analysis_data = {"metrics": metrics}
        return HighwindResultsManager(experiment)

    def test_reads_the_window_the_job_marked_as_summary(self):
        manager = self.manager(
            [
                metric(
                    "days_of_use",
                    [
                        window("cumulative", 0, 6, "confident", False),
                        window("cumulative", 0, 13, "forming", True),
                        window("cumulative", 0, 20, "not_started", False),
                    ],
                )
            ]
        )

        [result] = manager.get_metrics()

        self.assertEqual(result["window"]["end_day"], 13)
        self.assertEqual(result["window"]["span_days"], 14)

    def test_disjoint_window_span_counts_only_its_own_days(self):
        manager = self.manager(
            [metric("days_of_use", [window("disjoint", 7, 13, "confident", True)])]
        )

        [result] = manager.get_metrics()

        self.assertEqual(result["window"]["span_days"], 7)

    def test_metric_with_no_summary_window_has_none(self):
        manager = self.manager(
            [metric("days_of_use", [window("cumulative", 0, 6, "not_started", False)])]
        )

        [result] = manager.get_metrics()

        self.assertIsNone(result["window"])
        self.assertFalse(result["is_matured"])
        self.assertEqual(result["comparisons"], [])

    def test_settled_states_count_as_matured(self):
        for state in (HighwindCellState.FORMING, HighwindCellState.CONFIDENT):
            with self.subTest(state=state):
                manager = self.manager(
                    [metric("days_of_use", [window("cumulative", 0, 6, state, True)])]
                )

                [result] = manager.get_metrics()

                self.assertTrue(result["is_matured"])

    def test_unsettled_states_do_not_count_as_matured(self):
        for state in (
            HighwindCellState.NOT_STARTED,
            HighwindCellState.INSUFFICIENT_DATA,
            HighwindCellState.ERROR,
        ):
            with self.subTest(state=state):
                manager = self.manager(
                    [metric("days_of_use", [window("cumulative", 0, 6, state, True)])]
                )

                [result] = manager.get_metrics()

                self.assertFalse(result["is_matured"])

    def test_notable_metrics_are_the_confident_changes(self):
        manager = self.manager(
            [
                metric(
                    "moved",
                    [window("cumulative", 0, 6, "confident", True, direction="positive")],
                ),
                metric(
                    "flat",
                    [window("cumulative", 0, 6, "confident", True, direction="neutral")],
                ),
                metric(
                    "forming",
                    [window("cumulative", 0, 6, "forming", True, direction="positive")],
                ),
            ]
        )

        self.assertEqual(
            [m["slug"] for m in manager.get_notable_metrics()],
            ["moved"],
        )

    def test_friendly_name_comes_from_the_results_data(self):
        manager = self.manager(
            [
                metric("days_of_use", [], friendly_name="Days of use"),
                metric("unnamed", []),
            ]
        )

        names = {m["slug"]: m["friendly_name"] for m in manager.get_metrics()}

        self.assertEqual(names["days_of_use"], "Days of use")
        self.assertEqual(names["unnamed"], "unnamed")

    def test_enum_values_match_the_raw_json_strings(self):
        # The blob stores plain strings, so the comparisons above only hold because the
        # schema enums are str subclasses. If that ever changes, this fails first.
        self.assertEqual(HighwindCellState.CONFIDENT, "confident")
        self.assertEqual(HighwindDirection.NEUTRAL, "neutral")
