from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import TestCase, override_settings
from metric_config_parser.config import LocalConfigCollection

from experimenter.catalog import Catalog, check_catalog
from experimenter.catalog.tests.mock_catalog import mock_nimbus_configs
from experimenter.experiments.constants import NimbusConstants

DESKTOP = NimbusConstants.Application.DESKTOP
FENIX = NimbusConstants.Application.FENIX

DEFINITIONS_TOML = """
[metrics.uri_count]
data_source = "main"
aggregation = "sum"
column = "uri_count"
friendly_name = "URIs visited"
"""

DEFAULTS_TOML = """
[metrics.days_of_use]
data_source = "main"
aggregation = "sum"
column = "days_of_use"
"""

OUTCOME_TOML = """
[metrics.search_count]
data_source = "main"
aggregation = "sum"
column = "search_count"
"""

DATA_SOURCE_TOML = """
[data_sources.main]
from_expression = "mozdata.telemetry.main"
submission_date_column = "submission_date"
client_id_column = "client_id"
"""


class TestCatalog(TestCase):
    def setUp(self):
        Catalog.clear_cache()
        self.addCleanup(Catalog.clear_cache)

    def catalog(self, application=DESKTOP):
        return Catalog.by_application(application, nimbus_configs=mock_nimbus_configs())

    def test_the_catalog_is_every_metric_the_application_declares(self):
        catalog = self.catalog()

        self.assertEqual(
            [metric.slug for metric in catalog.metrics],
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
        [metric] = [m for m in self.catalog().metrics if m.slug == "uri_count"]

        self.assertEqual(metric.friendly_name, "URIs visited")
        self.assertEqual(metric.description, "URIs visited per client.")

    def test_a_metric_with_no_friendly_name_falls_back_to_its_slug(self):
        [metric] = [m for m in self.catalog().metrics if m.slug == "search_count"]

        self.assertEqual(metric.friendly_name, "search_count")

    def test_the_guardrails_are_the_metrics_in_the_defaults_file(self):
        self.assertEqual(self.catalog().guardrails, ["active_hours", "days_of_use"])

    def test_an_outcome_is_named_by_its_file_and_holds_exactly_its_metrics(self):
        outcomes = {o.slug: o.metrics for o in self.catalog().outcomes}

        self.assertEqual(
            outcomes,
            {
                "onboarding": ["first_run_retention"],
                "search": ["ad_clicks", "search_count"],
            },
        )

    def test_each_application_reads_only_its_own_files(self):
        catalog = self.catalog(FENIX)

        self.assertEqual([m.slug for m in catalog.metrics], ["fenix_uri_count"])
        self.assertEqual(catalog.guardrails, [])
        self.assertEqual(catalog.outcomes, [])

    def test_an_application_with_no_nimbus_files_has_an_empty_catalog(self):
        catalog = Catalog.by_application(
            NimbusConstants.Application.IOS, nimbus_configs=mock_nimbus_configs()
        )

        self.assertEqual(catalog.metrics, [])
        self.assertEqual(catalog.guardrails, [])
        self.assertEqual(catalog.outcomes, [])

    def test_an_application_outside_the_catalog_is_empty(self):
        Catalog.clear_cache()
        catalog = Catalog.by_application("not-an-application", nimbus_configs=[])

        self.assertEqual(catalog.application, "not-an-application")
        self.assertEqual(catalog.metrics, [])

    def test_the_catalog_is_only_loaded_once(self):
        first = Catalog.all(nimbus_configs=mock_nimbus_configs())

        self.assertIs(Catalog.all(nimbus_configs=[]), first)

    def test_the_check_reports_a_catalog_that_cannot_be_loaded(self):
        with patch.object(
            LocalConfigCollection, "from_local_path", side_effect=Exception("no checkout")
        ):
            errors = check_catalog(None)

        self.assertTrue(errors)
        self.assertIn("Error loading Catalog", errors[0].msg)

    def test_the_check_passes_on_a_catalog_that_loads(self):
        self.assertEqual(check_catalog(None, nimbus_configs=mock_nimbus_configs()), [])


class TestCatalogFromMetricHub(TestCase):
    # The one test that reads the directory layout, rather than configs handed to it.
    def setUp(self):
        Catalog.clear_cache()
        self.addCleanup(Catalog.clear_cache)

    def test_it_reads_definitions_defaults_and_outcomes_from_the_checkout(self):
        with TemporaryDirectory() as directory:
            nimbus = Path(directory) / "nimbus"
            (nimbus / "definitions").mkdir(parents=True)
            (nimbus / "defaults").mkdir(parents=True)
            (nimbus / "outcomes" / "firefox_desktop").mkdir(parents=True)
            (nimbus / "definitions" / "firefox_desktop.toml").write_text(
                DATA_SOURCE_TOML + DEFINITIONS_TOML
            )
            (nimbus / "defaults" / "firefox_desktop.toml").write_text(DEFAULTS_TOML)
            (nimbus / "outcomes" / "firefox_desktop" / "search.toml").write_text(
                OUTCOME_TOML
            )

            with override_settings(METRIC_HUB_NIMBUS_PATH=directory):
                catalog = Catalog.by_application(DESKTOP)

        self.assertEqual(
            [metric.slug for metric in catalog.metrics],
            ["days_of_use", "search_count", "uri_count"],
        )
        self.assertEqual(catalog.guardrails, ["days_of_use"])
        self.assertEqual([o.slug for o in catalog.outcomes], ["search"])
        self.assertEqual(catalog.outcomes[0].metrics, ["search_count"])
