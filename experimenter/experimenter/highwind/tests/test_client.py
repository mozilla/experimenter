import datetime
import io
from unittest import mock

from django.test import TestCase
from django.utils import timezone
from pydantic import ValidationError

from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.highwind.client import blob_path, get_analysis
from experimenter.highwind.tests import build_analysis_json


class TestBlobPath(TestCase):
    def test_hyphens_become_underscores(self):
        self.assertEqual(
            blob_path("my-experiment-slug"), "highwind/my_experiment_slug.json"
        )


@mock.patch("experimenter.highwind.client.analysis_storage")
class TestGetAnalysis(TestCase):
    def setUp(self):
        super().setUp()
        self.experiment = NimbusExperimentFactory.create(slug="test-experiment")
        self.generated_at = timezone.now()

    def test_returns_none_when_no_blob_written(self, mock_storage):
        mock_storage.exists.return_value = False

        self.assertIsNone(get_analysis(self.experiment))
        mock_storage.exists.assert_called_once_with("highwind/test_experiment.json")
        mock_storage.open.assert_not_called()

    def test_returns_validated_analysis(self, mock_storage):
        mock_storage.exists.return_value = True
        mock_storage.open.return_value = io.StringIO(
            build_analysis_json("test-experiment", self.generated_at)
        )

        analysis = get_analysis(self.experiment)

        self.assertEqual(analysis.metadata.experiment_slug, "test-experiment")
        self.assertEqual(analysis.metadata.generated_at, self.generated_at)

    def test_raises_for_a_blob_that_does_not_conform(self, mock_storage):
        mock_storage.exists.return_value = True
        mock_storage.open.return_value = io.StringIO('{"metadata": {}}')

        with self.assertRaises(ValidationError):
            get_analysis(self.experiment)

    def test_raises_for_an_unexpected_field(self, mock_storage):
        mock_storage.exists.return_value = True
        mock_storage.open.return_value = io.StringIO(
            build_analysis_json(
                "test-experiment",
                timezone.now() - datetime.timedelta(hours=1),
                unexpected="field",
            )
        )

        with self.assertRaises(ValidationError):
            get_analysis(self.experiment)
