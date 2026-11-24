from unittest.mock import patch

from django.test import TestCase
from metric_config_parser.config import LocalConfigCollection

from experimenter.experiments.constants import NimbusConstants
from experimenter.metrics import NimbusMetrics, check_nimbus_metrics
from experimenter.metrics.tests import mock_nimbus_metrics

DESKTOP = NimbusConstants.Application.DESKTOP
FENIX = NimbusConstants.Application.FENIX
IOS = NimbusConstants.Application.IOS


@mock_nimbus_metrics
class TestNimbusMetrics(TestCase):
    def setUp(self):
        NimbusMetrics.clear_cache()
        self.addCleanup(NimbusMetrics.clear_cache)

    def test_an_applications_metrics_are_every_metric_it_declares(self):
        metrics = NimbusMetrics.by_application(DESKTOP)

        self.assertEqual(
            [metric.slug for metric in metrics.metrics],
            [
                "active_hours",
                "ad_clicks",
                "days_of_use",
                "first_run_retention",
                "is_pinned",
                "search_count",
                "uri_count",
            ],
        )

    def test_a_metric_carries_the_name_and_description_it_was_given(self):
        metrics = NimbusMetrics.by_application(DESKTOP).metrics
        [uri_count] = [metric for metric in metrics if metric.slug == "uri_count"]

        self.assertEqual(uri_count.friendly_name, "URIs visited")
        self.assertEqual(uri_count.description, "URIs visited per client.")

    def test_a_metric_with_no_friendly_name_falls_back_to_its_slug(self):
        metrics = NimbusMetrics.by_application(DESKTOP).metrics
        [search_count] = [metric for metric in metrics if metric.slug == "search_count"]

        self.assertEqual(search_count.friendly_name, "search_count")

    def test_the_guardrails_are_the_metrics_in_the_defaults_file(self):
        metrics = NimbusMetrics.by_application(DESKTOP)

        self.assertEqual(metrics.guardrails, ["active_hours", "days_of_use"])

    def test_an_outcome_is_named_by_its_file_and_holds_exactly_its_metrics(self):
        outcomes = NimbusMetrics.by_application(DESKTOP).outcomes

        self.assertEqual(
            {outcome.slug: outcome.metrics for outcome in outcomes},
            {
                "onboarding": ["first_run_retention"],
                "search": ["ad_clicks", "search_count"],
            },
        )

    def test_an_application_reads_only_its_own_files(self):
        metrics = NimbusMetrics.by_application(FENIX)

        self.assertEqual([m.slug for m in metrics.metrics], ["fenix_uri_count"])
        self.assertEqual(metrics.guardrails, [])
        self.assertEqual(metrics.outcomes, [])

    def test_an_application_with_no_nimbus_files_has_nothing(self):
        metrics = NimbusMetrics.by_application(IOS)

        self.assertEqual(metrics.metrics, [])
        self.assertEqual(metrics.guardrails, [])
        self.assertEqual(metrics.outcomes, [])

    def test_an_application_outside_the_catalog_has_nothing(self):
        metrics = NimbusMetrics.by_application("not-an-application")

        self.assertEqual(metrics.application, "not-an-application")
        self.assertEqual(metrics.metrics, [])

    def test_they_are_only_loaded_once(self):
        first = NimbusMetrics.all()

        self.assertIs(NimbusMetrics.all(), first)

    def test_the_check_passes_on_metrics_that_load(self):
        self.assertEqual(check_nimbus_metrics(None), [])

    def test_the_check_reports_metrics_that_cannot_be_loaded(self):
        # A missing checkout reads as empty rather than raising, so this stands in for
        # a metric-hub the installed parser cannot read.
        with patch.object(
            LocalConfigCollection, "from_local_path", side_effect=Exception("no checkout")
        ):
            errors = check_nimbus_metrics(None)

        self.assertTrue(errors)
        self.assertIn("Error loading NimbusMetrics", errors[0].msg)
