import json
from unittest.mock import patch

from django.test import TestCase
from rust_fml import FmlClient

from experimenter.experiments.constants import NimbusConstants
from experimenter.features.manifests.nimbus_fml_loader import NimbusFmlLoader
from experimenter.features.tests import (
    FML_DIR,
    mock_fml_features,
    mock_fml_versioned_features,
)


class TestNimbusFmlLoader(TestCase):
    maxDiff = None

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
    @mock_fml_versioned_features
    def test_create_fml_client(self, new_client):
        new_client.return_value = None
        application = "fenix"
        channel = "release"
        version = "119.0.0"
        loader = self.create_loader(application, channel)

        expected_path = (
            FML_DIR
            / "versioned_features"
            / f"{application}"
            / f"v{version}"
            / f"{channel}.fml.yaml"
        )

        client = loader.fml_client(version=version)
        self.assertIsNotNone(client)
        new_client.assert_called()
        new_client.assert_called_with(str(expected_path), channel)

    @mock_fml_features
    def test_get_local_file_path_no_version(self):
        application = "fenix"
        channel = "nightly"
        loader = self.create_loader(application=application, channel=channel)
        expected_path = FML_DIR / f"{application}" / f"{channel}.fml.yaml"

        file_path = loader.file_path()
        self.assertEqual(file_path, expected_path)

    @mock_fml_versioned_features
    def test_get_local_file_path_for_nightly_with_version(self):
        application = "fenix"
        channel = "release"
        version = "119.0.0"
        expected_path = (
            FML_DIR
            / "versioned_features"
            / f"{application}"
            / f"v{version}"
            / f"{channel}.fml.yaml"
        )
        loader = self.create_loader(channel=channel)

        file_path = loader.file_path(version="119.0.0")
        self.assertEqual(file_path, expected_path)

    @mock_fml_versioned_features
    def test_get_local_file_path_for_invalid_channel(self):
        loader = self.create_loader(channel="rats")
        with self.assertLogs(level="ERROR") as log:
            file_path = loader.file_path(version="119.0.0")
            self.assertIsNone(file_path)
            self.assertIn("Nimbus FML Loader: Invalid manifest path", log.output[0])

    def test_get_local_file_path_does_not_exist(self):
        version = "1.2.3"
        loader = self.create_loader()
        with self.assertLogs(level="ERROR") as log:
            file_path = loader.file_path(version=version)
            self.assertIsNone(file_path)
            self.assertIn("Nimbus FML Loader: Invalid manifest path", log.output[0])

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

    def test_get_fml_errors_fetches_client_inspector_and_error(
        self,
    ):
        loader = self.create_loader()
        test_blob = json.dumps({"features": {"new-feature": {"enabled": "false"}}})

        result = loader.get_fml_errors(test_blob, "cookie-banners")
        expected_error = 'Invalid property "features"; did you mean "sections-enabled"?'
        self.assertIn(expected_error, result[0].message)

    @mock_fml_features
    def test_get_fml_errors_with_no_inspector(
        self,
    ):
        # an inspector will only be fetched for valid features
        fake_feature = "my-fake-feature"
        loader = self.create_loader()
        test_blob = json.dumps({"features": {"new-feature": {"enabled": "false"}}})
        result = loader.get_fml_errors(test_blob, fake_feature, "119.0.0")
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

    def test_return_empty_list_for_no_fml_errors(
        self,
    ):
        loader = self.create_loader()
        valid_blob = json.dumps({"sections-enabled": {"feature-ui": 2}})

        result = loader.get_fml_errors(valid_blob, "cookie-banners")
        self.assertEqual(result, [])

    def test_return_no_errors_for_invalid_application(
        self,
    ):
        application = "badapp"
        channel = "release"
        with self.assertLogs(level="ERROR") as log:
            loader = NimbusFmlLoader(application, channel)
            test_blob = json.dumps({"features": {"new-feature": {"enabled": "false"}}})

            result = loader.get_fml_errors(test_blob, "cookie-banners")

            self.assertEqual(loader.application, None)
            self.assertEqual(result, [])
            self.assertIn("Nimbus FML Loader: Invalid application", log.output[0])
