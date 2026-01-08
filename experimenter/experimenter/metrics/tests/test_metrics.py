from django.test import TestCase

from experimenter.experiments.models import NimbusExperiment
from experimenter.metrics import MetricAreas
from experimenter.metrics.tests import mock_valid_metrics


@mock_valid_metrics
class TestMetrics(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        MetricAreas.clear_cache()

    def test_load_all_metrics(self):
        metrics = MetricAreas.all()
        self.assertEqual(len(metrics), 2)

        expected = {
            "fenix": {"engagement": ["fenix_metric", "another_metric"]},
            "firefox_desktop": {
                "engagement": ["mock_engagement_metric", "another_metric"]
            },
        }

        self.assertEqual(metrics, expected)

    def test_get_metric_area_by_slug_and_application(self):
        area = MetricAreas.get(
            application=NimbusExperiment.Application.FENIX,
            slug="fenix_metric",
        )
        self.assertIsNotNone(area)
        self.assertEqual(area, "Engagement")

        missing_metric = MetricAreas.get(
            application=NimbusExperiment.Application.FENIX,
            slug="non_existent_metric",
        )
        self.assertIsNone(missing_metric)
