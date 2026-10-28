import datetime as dt

from django.test import TestCase
from mozilla_nimbus_schemas.highwind import HighwindCellState, HighwindDirection

from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.highwind.results import HighwindResultsManager
from experimenter.highwind.tests.factories import (
    build_analysis_data,
    build_metric,
    build_window,
)

REFERENCE = "control"
TREATMENT = "treatment"


class TestHighwindResultsManager(TestCase):
    def manager(self, metrics):
        experiment = NimbusExperimentFactory.create()
        experiment.analysis_data = build_analysis_data(metrics=metrics)
        return HighwindResultsManager(experiment)

    def one(self, metrics):
        [result] = self.manager(metrics).get_metrics()
        return result

    def with_window(self, **kwargs):
        return self.one([build_metric(windows=[build_window(**kwargs)])])

    def test_reads_the_window_the_job_marked_as_summary(self):
        result = self.one(
            [
                build_metric(
                    windows=[
                        build_window(end_day=6, is_summary=False),
                        build_window(end_day=13, is_summary=True),
                        build_window(end_day=20, is_summary=False),
                    ]
                )
            ]
        )

        self.assertEqual(result["window"]["end_day"], 13)
        self.assertEqual(result["window"]["span_days"], 14)

    def test_disjoint_window_span_counts_only_its_own_days(self):
        result = self.with_window(kind="disjoint", start_day=7, end_day=13)

        self.assertEqual(result["window"]["span_days"], 7)

    def test_matures_on_is_a_date_the_template_can_format(self):
        result = self.with_window(matures_on="2026-10-08")

        self.assertEqual(result["matures_on"], dt.date(2026, 10, 8))

    def test_metric_with_no_summary_window_has_none(self):
        result = self.with_window(is_summary=False)

        self.assertIsNone(result["window"])
        self.assertFalse(result["is_matured"])
        self.assertEqual(result["cells"], [])
        self.assertEqual(result["state"], HighwindCellState.NOT_STARTED)

    def test_a_metric_without_the_segment_has_no_window(self):
        result = self.one([build_metric(windows=[build_window()], segment="all_exposed")])

        self.assertIsNone(result["window"])
        self.assertFalse(result["has_results"])

    def test_reference_branch_cell_carries_no_comparison(self):
        result = self.with_window()

        cells = {cell["branch"]: cell for cell in result["cells"]}
        self.assertTrue(cells[REFERENCE]["is_reference"])
        self.assertIsNone(cells[REFERENCE]["relative"])
        self.assertFalse(cells[TREATMENT]["is_reference"])
        self.assertIsNotNone(cells[TREATMENT]["relative"])

    def test_relative_is_converted_to_the_fraction_the_card_expects(self):
        # The blob carries 1.25 meaning 1.25%, and the shared card multiplies by 100.
        result = self.with_window(relative=1.25)

        treatment = next(c for c in result["cells"] if not c["is_reference"])
        self.assertAlmostEqual(treatment["relative"]["point"], 0.0125)

    def test_settled_states_count_as_matured(self):
        for state in (HighwindCellState.FORMING, HighwindCellState.CONFIDENT):
            with self.subTest(state=state):
                self.assertTrue(self.with_window(state=state)["is_matured"])

    def test_unsettled_states_do_not_count_as_matured(self):
        for state in (
            HighwindCellState.NOT_STARTED,
            HighwindCellState.INSUFFICIENT_DATA,
            HighwindCellState.ERROR,
        ):
            with self.subTest(state=state):
                self.assertFalse(self.with_window(state=state)["is_matured"])

    def test_an_errored_or_insufficient_window_still_has_results_to_show(self):
        for state in (HighwindCellState.ERROR, HighwindCellState.INSUFFICIENT_DATA):
            with self.subTest(state=state):
                self.assertTrue(self.with_window(state=state)["has_results"])

    def test_a_window_that_has_not_started_has_nothing_to_show(self):
        result = self.with_window(state=HighwindCellState.NOT_STARTED)

        self.assertFalse(result["has_results"])

    def test_metric_state_is_the_state_of_its_cells(self):
        for state in (
            HighwindCellState.ERROR,
            HighwindCellState.CONFIDENT,
            HighwindCellState.FORMING,
            HighwindCellState.INSUFFICIENT_DATA,
            HighwindCellState.NOT_STARTED,
        ):
            with self.subTest(state=state):
                self.assertEqual(self.with_window(state=state)["state"], state)

    def test_notable_metrics_are_the_confident_changes(self):
        manager = self.manager(
            [
                build_metric(
                    "moved",
                    windows=[build_window(direction=HighwindDirection.POSITIVE)],
                ),
                build_metric(
                    "flat",
                    windows=[build_window(direction=HighwindDirection.NEUTRAL)],
                ),
                build_metric(
                    "forming",
                    windows=[
                        build_window(
                            state=HighwindCellState.FORMING,
                            direction=HighwindDirection.POSITIVE,
                        )
                    ],
                ),
            ]
        )

        self.assertEqual([m["slug"] for m in manager.get_notable_metrics()], ["moved"])

    def test_friendly_name_comes_from_the_results_data(self):
        manager = self.manager(
            [
                build_metric("days_of_use", friendly_name="Days of use", windows=[]),
                build_metric("unnamed", windows=[]),
            ]
        )

        names = {m["slug"]: m["friendly_name"] for m in manager.get_metrics()}

        self.assertEqual(names["days_of_use"], "Days of use")
        self.assertEqual(names["unnamed"], "unnamed")

    def test_a_later_forming_window_supersedes_an_earlier_confident_one(self):
        # Taken from a production blob, where days_of_use settled confidently at end_day
        # 20 and 27 then widened back to forming at 34. The grid follows the marked
        # window, so it reports forming and no notable change.
        result = self.one(
            [
                build_metric(
                    windows=[
                        build_window(
                            end_day=6, state=HighwindCellState.FORMING, is_summary=False
                        ),
                        build_window(
                            end_day=13, state=HighwindCellState.FORMING, is_summary=False
                        ),
                        build_window(
                            end_day=20,
                            state=HighwindCellState.CONFIDENT,
                            is_summary=False,
                        ),
                        build_window(
                            end_day=27,
                            state=HighwindCellState.CONFIDENT,
                            is_summary=False,
                        ),
                        build_window(
                            end_day=34,
                            state=HighwindCellState.FORMING,
                            direction=HighwindDirection.NEUTRAL,
                            is_summary=True,
                        ),
                        build_window(
                            end_day=41,
                            state=HighwindCellState.NOT_STARTED,
                            is_summary=False,
                        ),
                    ]
                )
            ]
        )

        self.assertEqual(result["window"]["end_day"], 34)
        self.assertEqual(result["window"]["span_days"], 35)
        self.assertEqual(result["state"], HighwindCellState.FORMING)
        self.assertFalse(result["has_confident_change"])

    def test_enum_values_match_the_raw_json_strings(self):
        # The comparisons above only hold while the schema enums subclass str.
        self.assertEqual(HighwindCellState.CONFIDENT, "confident")
        self.assertEqual(HighwindDirection.NEUTRAL, "neutral")
