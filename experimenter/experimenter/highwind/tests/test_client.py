import io
from unittest import mock

from django.test import TestCase
from django.utils import timezone
from pydantic import ValidationError

from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.highwind.client import (
    UnsupportedSchemaError,
    blob_path,
    get_analysis,
    list_analysis_blobs,
)
from experimenter.highwind.tests.factories import (
    build_analysis,
    build_legacy_analysis_json,
)


class TestBlobPath(TestCase):
    def test_hyphens_become_underscores(self):
        self.assertEqual(
            blob_path("my-experiment-slug"), "highwind/my_experiment_slug.json"
        )


@mock.patch("experimenter.highwind.client.analysis_storage")
class TestListAnalysisBlobs(TestCase):
    def test_lists_the_objects_under_the_prefix(self, mock_storage):
        mock_storage.listdir.return_value = ([], ["one.json", "two.json"])

        self.assertEqual(
            list_analysis_blobs(), {"highwind/one.json", "highwind/two.json"}
        )
        mock_storage.listdir.assert_called_once_with("highwind")

    def test_empty_prefix_lists_nothing(self, mock_storage):
        mock_storage.listdir.return_value = ([], [])

        self.assertEqual(list_analysis_blobs(), set())


@mock.patch("experimenter.highwind.client.analysis_storage")
class TestGetAnalysis(TestCase):
    def setUp(self):
        super().setUp()
        self.experiment = NimbusExperimentFactory.create(slug="test-experiment")
        self.generated_at = timezone.now()

    def written_blob(self):
        return io.StringIO(
            build_analysis("test-experiment", self.generated_at).model_dump_json()
        )

    def test_returns_none_when_no_blob_written(self, mock_storage):
        mock_storage.exists.return_value = False

        self.assertIsNone(get_analysis(self.experiment))
        mock_storage.exists.assert_called_once_with("highwind/test_experiment.json")
        mock_storage.open.assert_not_called()

    def test_returns_validated_analysis(self, mock_storage):
        mock_storage.exists.return_value = True
        mock_storage.open.return_value = self.written_blob()

        analysis = get_analysis(self.experiment)

        self.assertEqual(analysis.metadata.experiment_slug, "test-experiment")
        self.assertEqual(analysis.metadata.generated_at, self.generated_at)

    def test_raises_unsupported_for_a_blob_from_before_the_schema(self, mock_storage):
        mock_storage.exists.return_value = True
        mock_storage.open.return_value = io.StringIO(
            build_legacy_analysis_json("test-experiment")
        )

        with self.assertRaises(UnsupportedSchemaError):
            get_analysis(self.experiment)

    def test_raises_unsupported_for_a_blob_declaring_another_version(self, mock_storage):
        mock_storage.exists.return_value = True
        mock_storage.open.return_value = io.StringIO(
            '{"metadata": {"schema_version": 2}}'
        )

        with self.assertRaises(UnsupportedSchemaError):
            get_analysis(self.experiment)

    def test_raises_validation_error_for_a_versioned_blob_that_does_not_conform(
        self, mock_storage
    ):
        mock_storage.exists.return_value = True
        mock_storage.open.return_value = io.StringIO(
            '{"metadata": {"schema_version": 1}}'
        )

        with self.assertRaises(ValidationError):
            get_analysis(self.experiment)

    def test_raises_for_an_unexpected_field(self, mock_storage):
        mock_storage.exists.return_value = True
        mock_storage.open.return_value = io.StringIO(
            build_analysis("test-experiment", self.generated_at)
            .model_dump_json()
            .replace('{"metadata"', '{"unexpected": "field", "metadata"')
        )

        with self.assertRaises(ValidationError):
            get_analysis(self.experiment)
