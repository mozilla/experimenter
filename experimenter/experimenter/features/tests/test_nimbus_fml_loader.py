import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.test import TestCase
from rust_fml import FmlClient

from experimenter.experiments.constants import NimbusConstants
from experimenter.features.manifests.nimbus_fml_loader import NimbusFmlLoader
from experimenter.settings import BASE_DIR


class TestNimbusFmlLoader(TestCase):
    MANIFEST_PATH_NO_VERSION = Path(
        BASE_DIR, "features", "manifests", "fenix", "release.fml.yaml"
    )
    MANIFEST_PATH_WITH_VERSION = Path(
        BASE_DIR, "features", "manifests", "fenix", "v119.0.0", "nightly.fml.yaml"
    )

    def setUp(self):
        NimbusFmlLoader.create_loader.cache_clear()
        NimbusFmlLoader.fml_client.cache_clear()

    def create_loader(
        self,
        application: str = "fenix",
        channel: str = "release",
    ):
        return NimbusFmlLoader(
            application=application,
            channel=channel,
        )

    def test_intiate_new_fml_loader(self):
        application = "fenix"
        channel = "release"

        loader = NimbusFmlLoader(application, channel)

        self.assertEqual(loader.application, application)
        self.assertEqual(loader.channel, channel)

    def test_intiate_new_fml_loader_app_and_channel_do_not_exist(self):
        application = "badapp"
        channel = "releaseit"

        loader = NimbusFmlLoader(application, channel)

        self.assertIsNone(loader.application)
        self.assertIsNone(loader.channel)

    @patch(
        "rust_fml.FmlClient.__init__",
    )
    def test_create_fml_client(self, new_client):
        new_client.return_value = None
        application = "fenix"
        channel = "release"
        loader = self.create_loader(application, channel)
        expected_path = self.MANIFEST_PATH_NO_VERSION

        client = loader.fml_client()
        self.assertIsNotNone(client)
        new_client.assert_called()
        new_client.assert_called_with(str(expected_path), channel)

    def test_get_local_file_path_no_version(self):
        loader = self.create_loader()
        file_path = loader.file_path()
        self.assertEqual(file_path, self.MANIFEST_PATH_NO_VERSION)

    def test_get_local_file_path_for_nightly_with_version(self):
        loader = self.create_loader(channel="nightly")
        file_path = loader.file_path(version="119.0.0")
        self.assertEqual(file_path, self.MANIFEST_PATH_WITH_VERSION)

    def test_get_local_file_path_for_invalid_channel(self):
        loader = self.create_loader(channel="rats")
        file_path = loader.file_path(version="119.0.0")
        self.assertIsNone(file_path)

    @patch(
        "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader.MANIFEST_PATH",
    )
    def test_get_local_file_path_does_not_exist(self, mock_manifest_path):
        loader = self.create_loader()
        mock_manifest_path.return_value = Path(BASE_DIR, "fake", "path")
        file_path = loader.file_path()
        self.assertIsNone(file_path)

    def test_local_fml_files_do_not_exist_for_bad_app(self):
        application = "badapp"
        channel = "release"
        with self.assertLogs(level="ERROR") as log:
            loader = NimbusFmlLoader(application, channel)
            file_path = loader.file_path()
            self.assertIsNone(file_path)
            self.assertIn("Nimbus FML Loader: Invalid application", log.output[0])

    def test_local_fml_files_do_not_exist_for_version(self):
        application = "fenix"
        channel = "release"
        version = "119.9.9"
        with self.assertLogs(level="ERROR") as log:
            loader = NimbusFmlLoader(application, channel)
            file_path = loader.file_path(version=version)
            self.assertIsNone(file_path)
            self.assertIn("Nimbus FML Loader: Invalid manifest path", log.output[0])

    def test_create_client(self):
        loader = self.create_loader()
        result = loader.fml_client()
        self.assertIsInstance(result, FmlClient)

    @patch(
        "rust_fml.FmlClient.get_feature_inspector",
    )
    def test_get_feature_inspector_from_client(self, mock_get_inspector):
        loader = self.create_loader()
        client = loader.fml_client()

        result = loader.feature_inspector(client, "some_id")

        mock_get_inspector.assert_called_once_with("some_id")
        self.assertIsNotNone(result)

    @patch(
        "rust_fml.FmlFeatureInspector.get_errors",
    )
    def test_get_errors_from_fml_inspector(self, mock_get_errors):
        loader = self.create_loader()
        client = loader.fml_client()
        test_blob = str(json.dumps({"new-feature": "false"}))

        inspector = loader.feature_inspector(client, "nimbus-validation")
        result = loader._get_errors(inspector, test_blob)
        mock_get_errors.assert_called_once_with(test_blob)
        self.assertIsNotNone(result)

    @patch(
        "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader.feature_inspector",
    )
    @patch(
        "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader._get_errors",
    )
    def test_get_fml_errors_fetches_client_inspector_and_error(
        self, mock_get_errors, mock_feature_inspector
    ):
        fml_errors = [
            {
                "line": 2,
                "col": 0,
                "message": "Incorrect value",
                "highlight": "enabled",
            },
            {
                "line": 3,
                "col": 1,
                "message": "Incorrect value again",
                "highlight": "disabled",
            },
        ]
        mock_get_errors.return_value = fml_errors
        mock_feature_inspector.return_value = MagicMock()
        loader = self.create_loader()
        test_blob = json.dumps({"features": {"new-feature": {"enabled": "false"}}})

        result = loader.get_fml_errors(test_blob, "my_feature_id")

        mock_feature_inspector.assert_called()
        mock_get_errors.assert_called()
        self.assertIn(fml_errors[0]["message"], result[0]["message"])
        self.assertIn(fml_errors[1]["message"], result[1]["message"])

    @patch(
        "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader.feature_inspector",
    )
    @patch(
        "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader._get_errors",
    )
    def test_get_fml_errors_with_no_inspector(
        self, mock_get_errors, mock_feature_inspector
    ):
        fml_errors = [
            {
                "line": 2,
                "col": 0,
                "message": "Incorrect value",
                "highlight": "enabled",
            },
            {
                "line": 3,
                "col": 1,
                "message": "Incorrect value again",
                "highlight": "disabled",
            },
        ]
        mock_get_errors.return_value = fml_errors
        mock_feature_inspector.return_value = None
        loader = self.create_loader()
        test_blob = json.dumps({"features": {"new-feature": {"enabled": "false"}}})

        result = loader.get_fml_errors(test_blob, "my_feature_id")

        mock_feature_inspector.assert_called()
        mock_get_errors.assert_not_called()
        self.assertEqual(result, [])

    def test_get_fml_errors_with_no_client_because_of_no_manifest(
        self,
    ):
        application = NimbusConstants.Application.DEMO_APP
        channel = "release"
        with self.assertLogs(level="ERROR") as log:
            loader = NimbusFmlLoader(application, channel)
            test_blob = json.dumps({"features": {"new-feature": {"enabled": "false"}}})

            result = loader.get_fml_errors(test_blob, "my_feature_id")

            self.assertEqual(result, [])
            self.assertIn("Nimbus FML Loader: Invalid manifest path:", log.output[0])
            self.assertIn("Nimbus FML Loader: Failed to get FmlClient.", log.output[1])

    def test_get_fml_client_with_invalid_fm_path(
        self,
    ):
        application = NimbusConstants.Application.DEMO_APP
        channel = "release"
        with self.assertLogs(level="ERROR") as log:
            loader = NimbusFmlLoader(application, channel)
            result = loader.fml_client()
            self.assertIsNone(result)
            self.assertIn("Nimbus FML Loader: Invalid manifest path:", log.output[0])
            self.assertIn("Nimbus FML Loader: Failed to get FmlClient.", log.output[1])

    @patch(
        "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader.feature_inspector",
    )
    def test_return_empty_list_for_no_fml_errors(
        self,
        mock_feature_inspector,
    ):
        mock_feature_inspector.return_value = MagicMock()
        loader = self.create_loader()
        test_blob = json.dumps({"features": {"new-feature": {"enabled": "false"}}})
        with patch(
            "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader._get_errors",
        ) as mock_get_errors:
            mock_get_errors.return_value = None
            result = loader.get_fml_errors(test_blob, "my_feature_id")

            mock_feature_inspector.assert_called()
            mock_get_errors.assert_called()
            self.assertEqual(result, [])

    def test_return_no_errors_for_invalid_application(
        self,
    ):
        application = "badapp"
        channel = "release"
        with self.assertLogs(level="ERROR") as log:
            loader = NimbusFmlLoader(application, channel)
            test_blob = json.dumps({"features": {"new-feature": {"enabled": "false"}}})

            result = loader.get_fml_errors(test_blob, "my_feature_id")

            self.assertEqual(loader.application, None)
            self.assertEqual(result, [])
            self.assertIn("Nimbus FML Loader: Invalid application", log.output[0])
