import datetime as dt

from django.test import TestCase
from mozilla_nimbus_schemas.highwind import (
    HighwindCellState,
    HighwindDirection,
    HighwindWinsorizeMode,
)

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.highwind.results import HighwindResultsManager, MetricDirection
from experimenter.highwind.tests.factories import (
    build_analysis_data,
    build_interval,
    build_metric,
    build_window,
)
from experimenter.metrics import NimbusMetrics
from experimenter.metrics.tests import mock_nimbus_metrics

REFERENCE = "control"
TREATMENT = "treatment"

# From the catalog fixtures: a ratio, and one that is not.
RATIO_METRIC = "ad_click_rate"
COUNT_METRIC = "uri_count"


@mock_nimbus_metrics
class HighwindResultsTestCase(TestCase):
    def setUp(self):
        NimbusMetrics.clear_cache()
        self.addCleanup(NimbusMetrics.clear_cache)

    def manager(self, metrics):
        experiment = NimbusExperimentFactory.create(
            application=NimbusConstants.Application.DESKTOP
        )
        experiment.analysis_data = build_analysis_data(metrics=metrics)
        return HighwindResultsManager(experiment)

    def only_metric(self, metrics):
        [result] = self.manager(metrics).get_metrics()
        return result

    def metric_with_window(self, slug=COUNT_METRIC, **kwargs):
        return self.only_metric(
            [build_metric(slug=slug, windows=[build_window(**kwargs)])]
        )

    def only_window(self, **kwargs):
        return self.metric_with_window(**kwargs)["windows"][0]


class TestHighwindWindowStack(HighwindResultsTestCase):
    def test_every_window_the_job_reported_is_shown(self):
        result = self.only_metric(
            [
                build_metric(
                    windows=[
                        build_window(end_day=6),
                        build_window(end_day=13),
                        build_window(end_day=20),
                    ]
                )
            ]
        )

        self.assertEqual([window["end_day"] for window in result["windows"]], [6, 13, 20])

    def test_a_cumulative_window_is_named_by_the_days_it_covers(self):
        self.assertEqual(self.only_window(end_day=13)["label"], "first 14 days")

    def test_a_disjoint_window_is_named_by_both_its_ends(self):
        window = self.only_window(kind="disjoint", start_day=7, end_day=13)

        self.assertEqual(window["label"], "days 7\u201313")
        self.assertEqual(window["span_days"], 7)

    def test_each_window_carries_its_own_state(self):
        result = self.only_metric(
            [
                build_metric(
                    windows=[
                        build_window(end_day=6, state=HighwindCellState.CONFIDENT),
                        build_window(end_day=13, state=HighwindCellState.FORMING),
                        build_window(end_day=20, state=HighwindCellState.NOT_STARTED),
                    ]
                )
            ]
        )

        self.assertEqual(
            [window["state"] for window in result["windows"]],
            [
                HighwindCellState.CONFIDENT,
                HighwindCellState.FORMING,
                HighwindCellState.NOT_STARTED,
            ],
        )

    def test_a_metric_without_the_segment_reports_no_windows(self):
        result = self.only_metric(
            [build_metric(windows=[build_window()], segment="all_exposed")]
        )

        self.assertEqual(result["windows"], [])
        self.assertFalse(result["has_results"])

    def test_matures_on_is_the_next_window_still_to_come(self):
        result = self.only_metric(
            [
                build_metric(
                    windows=[
                        build_window(end_day=6, state=HighwindCellState.CONFIDENT),
                        build_window(
                            end_day=13,
                            state=HighwindCellState.NOT_STARTED,
                            matures_on="2026-10-08",
                        ),
                        build_window(
                            end_day=20,
                            state=HighwindCellState.NOT_STARTED,
                            matures_on="2026-10-15",
                        ),
                    ]
                )
            ]
        )

        self.assertEqual(result["matures_on"], dt.date(2026, 10, 8))

    def test_one_scale_covers_every_window_of_a_metric(self):
        # The widest interval across the metric sets the scale, so a window that
        # narrows draws a shorter bar instead of being redrawn to fill the same width.
        wide = build_window(end_day=6)
        narrow = build_window(end_day=13)
        wide.comparisons[0].relative = build_interval(1.0, spread=2.0)
        narrow.comparisons[0].relative = build_interval(1.0, spread=0.5)

        result = self.only_metric([build_metric(windows=[wide, narrow])])

        widths = [
            window["bar_geometry"][TREATMENT]["bar_width"] for window in result["windows"]
        ]
        self.assertGreater(widths[0], widths[1])

    def test_a_window_with_no_change_to_draw_has_no_geometry(self):
        window = self.only_window(
            state=HighwindCellState.NOT_STARTED, value=None, relative=None
        )

        self.assertEqual(window["bar_geometry"], {})

    def test_reference_branch_cell_carries_no_comparison(self):
        cells = {cell["branch"]: cell for cell in self.only_window()["cells"]}

        self.assertTrue(cells[REFERENCE]["is_reference"])
        self.assertIsNone(cells[REFERENCE]["relative"])
        self.assertFalse(cells[TREATMENT]["is_reference"])
        self.assertIsNotNone(cells[TREATMENT]["relative"])

    def test_relative_is_converted_to_the_fraction_the_card_expects(self):
        # The blob carries 1.25 meaning 1.25%, and the shared card multiplies by 100.
        window = self.only_window(relative=1.25)

        treatment = next(c for c in window["cells"] if not c["is_reference"])
        self.assertAlmostEqual(treatment["relative"]["point"], 0.0125)

    def test_an_errored_or_insufficient_window_still_has_results_to_show(self):
        for state in (HighwindCellState.ERROR, HighwindCellState.INSUFFICIENT_DATA):
            with self.subTest(state=state):
                self.assertTrue(self.metric_with_window(state=state)["has_results"])

    def test_a_metric_whose_windows_have_not_started_has_nothing_to_show(self):
        result = self.metric_with_window(state=HighwindCellState.NOT_STARTED)

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
                self.assertEqual(self.metric_with_window(state=state)["state"], state)

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

    def test_a_metric_is_notable_on_any_window_that_moved(self):
        # Not only the deepest one, which is what the page used to read.
        manager = self.manager(
            [
                build_metric(
                    windows=[
                        build_window(
                            end_day=6,
                            state=HighwindCellState.CONFIDENT,
                            direction=HighwindDirection.POSITIVE,
                        ),
                        build_window(end_day=13, state=HighwindCellState.FORMING),
                    ]
                )
            ]
        )

        self.assertEqual(len(manager.get_notable_metrics()), 1)

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

    def test_enum_values_match_the_raw_json_strings(self):
        # The comparisons above only hold while the schema enums subclass str.
        self.assertEqual(HighwindCellState.CONFIDENT, "confident")
        self.assertEqual(HighwindDirection.NEUTRAL, "neutral")


class TestHighwindHeadline(HighwindResultsTestCase):
    def ratio_with_windows(self, windows):
        return self.only_metric([build_metric(slug=RATIO_METRIC, windows=windows)])

    def test_a_metric_that_is_not_a_ratio_has_no_headline(self):
        result = self.metric_with_window(slug=COUNT_METRIC)

        self.assertFalse(result["is_ratio"])
        self.assertIsNone(result["headline"])

    def test_a_metric_missing_from_the_catalog_has_no_headline(self):
        result = self.metric_with_window(slug="not_in_the_catalog")

        self.assertFalse(result["is_ratio"])
        self.assertIsNone(result["headline"])

    def test_a_ratios_headline_is_its_deepest_confident_window(self):
        result = self.ratio_with_windows(
            [
                build_window(end_day=6, state=HighwindCellState.CONFIDENT),
                build_window(end_day=13, state=HighwindCellState.CONFIDENT),
                build_window(end_day=20, state=HighwindCellState.FORMING),
                build_window(end_day=27, state=HighwindCellState.NOT_STARTED),
            ]
        )

        self.assertTrue(result["is_ratio"])
        self.assertEqual(result["headline"]["end_day"], 13)
        self.assertEqual(result["headline"]["state"], HighwindCellState.CONFIDENT)

    def test_with_nothing_confident_the_headline_is_the_latest_matured_window(self):
        result = self.ratio_with_windows(
            [
                build_window(end_day=6, state=HighwindCellState.FORMING),
                build_window(end_day=13, state=HighwindCellState.FORMING),
                build_window(end_day=20, state=HighwindCellState.NOT_STARTED),
            ]
        )

        self.assertEqual(result["headline"]["end_day"], 13)
        self.assertEqual(result["headline"]["state"], HighwindCellState.FORMING)

    def test_a_ratio_with_nothing_matured_has_no_headline(self):
        result = self.ratio_with_windows(
            [
                build_window(end_day=6, state=HighwindCellState.NOT_STARTED),
                build_window(end_day=13, state=HighwindCellState.NOT_STARTED),
            ]
        )

        self.assertIsNone(result["headline"])


class TestHighwindPrecision(HighwindResultsTestCase):
    def precision_for(self, value):
        return self.metric_with_window(value=value, spread=value / 100)["precision"]

    def test_a_rate_keeps_enough_decimals_to_differ(self):
        # 0.9746 would read as "0.97 - 0.97" at two decimals.
        self.assertEqual(self.precision_for(0.9746), 4)

    def test_a_count_does_not_need_them(self):
        self.assertEqual(self.precision_for(5103.167), 1)

    def test_a_small_count_keeps_two(self):
        self.assertEqual(self.precision_for(22.6), 2)


class TestHighwindMetricDirection(HighwindResultsTestCase):
    def direction_for(self, **kwargs):
        return self.metric_with_window(**kwargs)["direction"]

    def test_a_confident_change_reports_its_direction(self):
        for direction in (HighwindDirection.POSITIVE, HighwindDirection.NEGATIVE):
            with self.subTest(direction=direction):
                self.assertEqual(
                    self.direction_for(
                        state=HighwindCellState.CONFIDENT, direction=direction
                    ),
                    direction,
                )

    def test_an_unsettled_metric_reports_no_direction(self):
        self.assertEqual(
            self.direction_for(
                state=HighwindCellState.FORMING, direction=HighwindDirection.POSITIVE
            ),
            HighwindDirection.NEUTRAL,
        )

    def test_treatments_moving_opposite_ways_report_mixed(self):
        window = build_window(
            state=HighwindCellState.CONFIDENT,
            direction=HighwindDirection.POSITIVE,
            treatments=("up", "down"),
        )
        window.comparisons[1].direction = HighwindDirection.NEGATIVE

        [result] = self.manager([build_metric(windows=[window])]).get_metrics()

        self.assertEqual(result["direction"], MetricDirection.MIXED)


class TestHighwindWinsorization(HighwindResultsTestCase):
    def test_a_clipped_window_reports_its_mode_and_both_thresholds(self):
        window = self.only_window(
            winsorize_mode=HighwindWinsorizeMode.FRACTION,
            post_winsorize_threshold=12.5,
            pre_winsorize_threshold=9.25,
        )

        self.assertEqual(
            window["winsorization"],
            {
                "mode": HighwindWinsorizeMode.FRACTION,
                "post_threshold": 12.5,
                "pre_threshold": 9.25,
                "clipped": [],
            },
        )

    def test_an_unclipped_window_reports_off_with_no_thresholds(self):
        window = self.only_window(winsorize_mode=HighwindWinsorizeMode.OFF)

        self.assertEqual(window["winsorization"]["mode"], HighwindWinsorizeMode.OFF)
        self.assertIsNone(window["winsorization"]["post_threshold"])
        self.assertIsNone(window["winsorization"]["pre_threshold"])

    def test_a_blob_without_the_fields_reports_no_winsorization(self):
        # Blobs written before the fields existed, which the schema still accepts.
        self.assertIsNone(self.only_window(winsorize_mode=None)["winsorization"])

    def test_only_the_branches_that_lost_values_are_reported(self):
        window = build_window(
            winsorize_mode=HighwindWinsorizeMode.FRACTION,
            post_winsorize_threshold=12.5,
            clipped_share=0.004,
        )
        window.branches[1].clipped_share = 0.0

        [result] = self.manager([build_metric(windows=[window])]).get_metrics()

        self.assertEqual(
            result["windows"][0]["winsorization"]["clipped"],
            [{"branch": REFERENCE, "share": 0.004}],
        )
