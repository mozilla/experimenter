import datetime as dt

from django.test import TestCase
from mozilla_nimbus_schemas.highwind import HighwindCellState, HighwindDirection

from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.highwind.results import HighwindResultsManager

REFERENCE = "control"
TREATMENT = "treatment"


def interval(point=1.0, lower=0.5, upper=1.5):
    return {"point": point, "lower": lower, "upper": upper}


def window(
    kind="cumulative",
    start_day=0,
    end_day=6,
    state=HighwindCellState.CONFIDENT,
    is_summary=True,
    direction=HighwindDirection.POSITIVE,
    relative=None,
    error=None,
    matures_on="2026-10-08",
):
    return {
        "window": {
            "kind": kind,
            "start_day": start_day,
            "end_day": end_day,
            "matures_on": matures_on,
        },
        "is_summary": is_summary,
        "branches": [
            {"branch": REFERENCE, "n": 100, "value": interval()},
            {"branch": TREATMENT, "n": 200, "value": interval()},
        ],
        "comparisons": [
            {
                "branch": TREATMENT,
                "reference_branch": REFERENCE,
                "state": state,
                "direction": direction,
                "relative": interval() if relative is None else relative,
                "absolute": interval(),
                "n_reference": 100,
                "n_treatment": 200,
                "error": error,
            }
        ],
    }


def metric(slug, windows, friendly_name=None, description=None):
    return {
        "slug": slug,
        "friendly_name": friendly_name or slug,
        "description": description,
        "segments": [{"segment": "all_enrolled", "windows": windows}],
    }


class TestHighwindResultsManager(TestCase):
    def manager(self, metrics):
        experiment = NimbusExperimentFactory.create()
        experiment.analysis_data = {
            "metadata": {"reference_branch": REFERENCE},
            "metrics": metrics,
        }
        return HighwindResultsManager(experiment)

    def one(self, metrics):
        [result] = self.manager(metrics).get_metrics()
        return result

    def test_reads_the_window_the_job_marked_as_summary(self):
        result = self.one(
            [
                metric(
                    "days_of_use",
                    [
                        window(end_day=6, is_summary=False),
                        window(end_day=13, is_summary=True),
                        window(end_day=20, is_summary=False),
                    ],
                )
            ]
        )

        self.assertEqual(result["window"]["end_day"], 13)
        self.assertEqual(result["window"]["span_days"], 14)

    def test_disjoint_window_span_counts_only_its_own_days(self):
        result = self.one(
            [metric("days_of_use", [window(kind="disjoint", start_day=7, end_day=13)])]
        )

        self.assertEqual(result["window"]["span_days"], 7)

    def test_matures_on_is_a_date_the_template_can_format(self):
        result = self.one([metric("days_of_use", [window(matures_on="2026-10-08")])])

        self.assertEqual(result["matures_on"], dt.date(2026, 10, 8))

    def test_metric_with_no_summary_window_has_none(self):
        result = self.one([metric("days_of_use", [window(is_summary=False)])])

        self.assertIsNone(result["window"])
        self.assertFalse(result["is_matured"])
        self.assertEqual(result["cells"], [])
        self.assertEqual(result["state"], HighwindCellState.NOT_STARTED)

    def test_a_metric_without_the_segment_has_no_window(self):
        other_segment = metric("days_of_use", [window()])
        other_segment["segments"][0]["segment"] = "all_exposed"

        result = self.one([other_segment])

        self.assertIsNone(result["window"])
        self.assertFalse(result["has_results"])

    def test_reference_branch_cell_carries_no_comparison(self):
        result = self.one([metric("days_of_use", [window()])])

        cells = {cell["branch"]: cell for cell in result["cells"]}
        self.assertTrue(cells[REFERENCE]["is_reference"])
        self.assertIsNone(cells[REFERENCE]["relative"])
        self.assertEqual(cells[REFERENCE]["absolute"], interval())
        self.assertFalse(cells[TREATMENT]["is_reference"])
        self.assertEqual(cells[TREATMENT]["relative"], interval())

    def test_settled_states_count_as_matured(self):
        for state in (HighwindCellState.FORMING, HighwindCellState.CONFIDENT):
            with self.subTest(state=state):
                result = self.one([metric("days_of_use", [window(state=state)])])

                self.assertTrue(result["is_matured"])

    def test_unsettled_states_do_not_count_as_matured(self):
        for state in (
            HighwindCellState.NOT_STARTED,
            HighwindCellState.INSUFFICIENT_DATA,
            HighwindCellState.ERROR,
        ):
            with self.subTest(state=state):
                result = self.one([metric("days_of_use", [window(state=state)])])

                self.assertFalse(result["is_matured"])

    def test_metric_state_is_the_state_of_its_cells(self):
        for state in (
            HighwindCellState.ERROR,
            HighwindCellState.CONFIDENT,
            HighwindCellState.FORMING,
            HighwindCellState.INSUFFICIENT_DATA,
            HighwindCellState.NOT_STARTED,
        ):
            with self.subTest(state=state):
                result = self.one([metric("days_of_use", [window(state=state)])])

                self.assertEqual(result["state"], state)

    def test_an_errored_or_insufficient_window_still_has_results_to_show(self):
        for state in (HighwindCellState.ERROR, HighwindCellState.INSUFFICIENT_DATA):
            with self.subTest(state=state):
                result = self.one([metric("days_of_use", [window(state=state)])])

                self.assertFalse(result["is_matured"])
                self.assertTrue(result["has_results"])

    def test_a_window_that_has_not_started_has_nothing_to_show(self):
        result = self.one(
            [metric("days_of_use", [window(state=HighwindCellState.NOT_STARTED)])]
        )

        self.assertFalse(result["has_results"])

    def test_notable_metrics_are_the_confident_changes(self):
        manager = self.manager(
            [
                metric("moved", [window(direction=HighwindDirection.POSITIVE)]),
                metric("flat", [window(direction=HighwindDirection.NEUTRAL)]),
                metric(
                    "forming",
                    [
                        window(
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
                metric("days_of_use", [], friendly_name="Days of use"),
                metric("unnamed", []),
            ]
        )

        names = {m["slug"]: m["friendly_name"] for m in manager.get_metrics()}

        self.assertEqual(names["days_of_use"], "Days of use")
        self.assertEqual(names["unnamed"], "unnamed")

    def test_a_later_forming_window_supersedes_an_earlier_confident_one(self):
        # Taken from a production blob, where days_of_use settled confidently at end_day
        # 20 and 27 then widened back to forming at 34. The grid follows the marked
        # window, so it reports forming and no notable change.
        windows = [
            window(end_day=6, state=HighwindCellState.FORMING, is_summary=False),
            window(end_day=13, state=HighwindCellState.FORMING, is_summary=False),
            window(
                end_day=20,
                state=HighwindCellState.CONFIDENT,
                direction=HighwindDirection.POSITIVE,
                is_summary=False,
            ),
            window(
                end_day=27,
                state=HighwindCellState.CONFIDENT,
                direction=HighwindDirection.POSITIVE,
                is_summary=False,
            ),
            window(
                end_day=34,
                state=HighwindCellState.FORMING,
                direction=HighwindDirection.NEUTRAL,
                is_summary=True,
                relative={
                    "point": 0.1407760527822436,
                    "lower": -0.04329428236937145,
                    "upper": 0.3248463879338586,
                },
            ),
            window(end_day=41, state=HighwindCellState.NOT_STARTED, is_summary=False),
        ]

        result = self.one([metric("days_of_use", windows)])

        self.assertEqual(result["window"]["end_day"], 34)
        self.assertEqual(result["window"]["span_days"], 35)
        self.assertEqual(result["state"], HighwindCellState.FORMING)
        self.assertFalse(result["has_confident_change"])
        treatment = next(c for c in result["cells"] if not c["is_reference"])
        # Already a percentage: 0.14 means 0.14%, not 14%.
        self.assertAlmostEqual(treatment["relative"]["point"], 0.1407760527822436)

    def test_enum_values_match_the_raw_json_strings(self):
        # The comparisons above only hold while the schema enums subclass str.
        self.assertEqual(HighwindCellState.CONFIDENT, "confident")
        self.assertEqual(HighwindDirection.NEUTRAL, "neutral")
