from django.core.checks import Error
from django.test import TestCase

from experimenter.experiments.models import NimbusExperiment
from experimenter.metrics import Metric, Metrics, check_metrics_tomls
from experimenter.metrics.tests import mock_invalid_metrics, mock_valid_metrics


@mock_valid_metrics
class TestMetrics(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Metrics.clear_cache()

    def test_load_all_metrics(self):
        metrics = Metrics.all()
        self.assertEqual(len(metrics), 2)
        self.assertIn(
            Metric(
                slug="some_metric",
                friendly_name="Some Metric",
                description="Description of some metric",
                metric_area="KPI",
                application=NimbusExperiment.Application.FENIX,
            ),
            metrics,
        )
        self.assertIn(
            Metric(
                slug="awesome_measure",
                friendly_name="Awesome Level",
                description="A measure of an experiment's objective awesomeness",
                metric_area="Engagement",
                application=NimbusExperiment.Application.DESKTOP.replace("-", "_"),
            ),
            metrics,
        )

    def test_get_metric_by_slug_and_application(self):
        metric = Metrics.get_by_slug_and_application(
            "some_metric",
            application=NimbusExperiment.Application.FENIX,
        )
        self.assertIsNotNone(metric)
        self.assertEqual(metric.friendly_name, "Some Metric")

        missing_metric = Metrics.get_by_slug_and_application(
            "non_existent_metric",
            application=NimbusExperiment.Application.DESKTOP,
        )
        self.assertIsNone(missing_metric)


class TestCheckMetricTOMLs(TestCase):
    def setUp(self):
        Metrics.clear_cache()

    @mock_valid_metrics
    def test_valid_metrics_do_not_trigger_check_error(self):
        errors = check_metrics_tomls(None)
        self.assertEqual(errors, [])

    @mock_invalid_metrics
    def test_invalid_metrics_do_trigger_check_error(self):
        errors = check_metrics_tomls(None)
        self.assertEqual(
            errors,
            [Error(msg="Error loading Metric TOMLs: 'friendly_name'")],
        )
