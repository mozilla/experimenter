import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.test import TestCase
from packaging import version
from rust_fml import FmlClient

from experimenter.features.manifests.nimbus_fml_loader import NimbusFmlLoader
from experimenter.settings import BASE_DIR


class TestNimbusFmlLoader(TestCase):
    TEST_BASE_PATH = (
        Path(BASE_DIR) / "features" / "tests" / "fixtures" / "fml" / "test_apps.yaml"
    )
    TEST_MANIFEST_PATH = (
        Path(BASE_DIR)
        / "features"
        / "tests"
        / "fixtures"
        / "fml"
        / "test_release.fml.yaml"
    )

    @staticmethod
    def create_loader(
        application: str = "fenix",
        channel: str = "release",
        path=TEST_BASE_PATH,
    ):
        return NimbusFmlLoader(
            application=application,
            channel=channel,
            file_location=path,
        )

    def test_intiate_new_fml_loader(self):
        application = "fenix"
        channel = "release"
        expected_repo = r"mozilla-mobile/firefox-android"

        loader = NimbusFmlLoader(application, channel, self.TEST_BASE_PATH)

        self.assertEqual(loader.application, application)
        self.assertEqual(loader.channel, channel)
        self.assertEqual(loader.application_data["repo"]["name"], expected_repo)

    def test_get_application_data_from_file(self):
        application = "fenix"
        expected_repo = r"mozilla-mobile/firefox-android"
        expected_fml = "fenix/app/nimbus.fml.yaml"

        data = NimbusFmlLoader._get_application_data(
            application_name=application, file_location=self.TEST_BASE_PATH
        )
        self.assertEqual(data["repo"]["name"], expected_repo)
        self.assertEqual(data["fml_path"], expected_fml)

    def test_get_application_data_does_not_exist(self):
        application = "garfield"

        data = NimbusFmlLoader._get_application_data(
            application_name=application, file_location=self.TEST_BASE_PATH
        )
        self.assertIsNone(data)

    def test_get_application_path_does_not_exist(self):
        application = "garfield"
        path = Path(BASE_DIR) / "features" / "garfield" / "bingo.yaml"

        data = NimbusFmlLoader._get_application_data(
            application_name=application, file_location=path
        )
        self.assertIsNone(data)

    def test_get_ref_no_versions(self):
        application = "fenix"
        channel = "release"
        no_version = []

        client = self.create_loader()
        refs = client._get_version_refs(no_version)

        self.assertEqual(client.application, application)
        self.assertEqual(client.channel, channel)
        self.assertEqual(refs, ["main"])

    def test_get_ref_for_single_version(self):
        application = "fenix"
        channel = "release"
        version = ["112.1.0"]

        client = self.create_loader()
        refs = client._get_version_refs(version)

        self.assertEqual(client.application, application)
        self.assertEqual(client.channel, channel)
        self.assertEqual(len(refs), 1)

    def test_get_refs_for_multiple_versions(self):
        application = "fenix"
        channel = "release"
        expected_repo = r"mozilla-mobile/firefox-android"
        versions = [
            "112.1.0",
            "112.1.1",
            "113.0.0",
            "118.7.3",
        ]

        client = self.create_loader()
        self.assertEqual(client.application_data["repo"]["name"], expected_repo)

        refs = client._get_version_refs(versions)

        self.assertEqual(client.application, application)
        self.assertEqual(client.channel, channel)
        self.assertEqual(len(refs), 4)

    def test_get_major_version_refs(self):
        loader = self.create_loader()
        v = version.parse("112.1.0")
        expected = "releases_v112"

        result = loader._get_major_version_ref(v)
        self.assertEqual(result, expected)

    def test_get_minor_version_refs(self):
        loader = self.create_loader()
        v = version.parse("112.1.0")
        expected = "fenix-v112.1.0"

        result = loader._get_minor_version_ref(v)
        self.assertEqual(result, expected)

    def test_get_major_version_refs_application_is_none(self):
        v = version.parse("112.1.0")
        loader = self.create_loader()
        loader.application_data = None
        result = loader._get_major_version_ref(version=v)
        self.assertIsNone(result)

    def test_get_minor_version_refs_application_is_none(self):
        v = version.parse("112.1.0")
        loader = self.create_loader()
        loader.application_data = None
        result = loader._get_minor_version_ref(version=v)
        self.assertIsNone(result)

    def test_get_fml_clients(self):
        versions = [
            "112.1.0",
            "112.1.1",
            "113.0.0",
            "118.7.3",
        ]
        loader = self.create_loader()

        with patch(
            "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader._create_client",
        ) as create:
            result = loader._get_fml_clients(versions)
            self.assertEqual(len(result), 4)
            create.assert_called()

    @patch(
        "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader._create_client",
    )
    @patch(
        "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader._get_local_file_path",
    )
    def test_get_fml_client_no_versions(self, mock_file_path, mock_create_client):
        no_version = []
        path = str(self.TEST_MANIFEST_PATH)
        mock_file_path.return_value = path
        mock_create_client.return_value = MagicMock(spec=FmlClient)
        expected_channel = "release"
        loader = self.create_loader()

        result = loader._get_fml_clients(no_version)
        self.assertEqual(len(result), 1)
        mock_create_client.assert_called()
        mock_file_path.assert_called()
        mock_create_client.assert_called_with(path, expected_channel)

    @patch(
        "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader._create_client",
    )
    def test_fetch_clients_returns_none(
        self,
        mock_create_client,
    ):
        mock_create_client.return_value = None
        versions = ["112.1.0"]
        loader = self.create_loader()

        result = loader._get_fml_clients(versions)
        self.assertEqual(result, [])
        mock_create_client.assert_called()

    @patch(
        "rust_fml.FmlClient.__init__",
    )
    def test_create_fml_client(self, new_client):
        new_client.return_value = None
        application = "fenix"
        path = str(self.TEST_MANIFEST_PATH)
        channel = "release"
        loader = self.create_loader(application, channel)

        loader._create_client(path, channel)
        new_client.assert_called()
        new_client.assert_called_with(path, channel)

    def test_get_local_file_path(self):
        expected_path = Path(
            r"/experimenter/experimenter/features/manifests/fenix/release.fml.yaml"
        )

        loader = self.create_loader()
        file_path = loader._get_local_file_path()
        self.assertEqual(file_path, expected_path)

    @patch(
        "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader.MANIFEST_PATH",
    )
    def test_get_local_file_path_does_not_exist(self, mock_manifest_path):
        loader = self.create_loader()
        mock_manifest_path.return_value = Path(BASE_DIR) / "fake" / "path"
        file_path = loader._get_local_file_path()
        self.assertIsNone(file_path)

    def test_get_remote_file_path(self):
        expected_path = Path(r"mozilla-mobile/firefox-android/fenix/app/nimbus.fml.yaml")
        loader = self.create_loader()
        file_path = loader._get_remote_file_path()
        self.assertEqual(file_path, expected_path)

    def test_get_remote_file_path_no_application_data(self):
        loader = self.create_loader()
        loader.application_data = None
        file_path = loader._get_remote_file_path()
        self.assertIsNone(file_path)

    @patch(
        "rust_fml.FmlClient.__init__",
    )
    def test_create_client(self, mock_fml_client):
        mock_fml_client.return_value = None
        loader = self.create_loader()
        result = loader._create_client("some/path", "release")
        mock_fml_client.assert_called()
        self.assertIsInstance(result, FmlClient)

    @patch(
        "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader._get_fml_clients",
    )
    @patch(
        "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader._get_inspectors",
    )
    @patch(
        "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader._get_errors",
    )
    def test_get_fml_errors_fetches_client_inspector_and_error(
        self, mock_get_clients, mock_get_inspectors, mock_get_errors
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
        mock_get_clients.return_value = fml_errors
        mock_get_inspectors.return_value = [MagicMock()]
        loader = self.create_loader()
        test_blob = json.dumps({"features": {"new-feature": {"enabled": "false"}}})

        result = loader.get_fml_errors(test_blob, "my_feature_id")

        mock_get_clients.assert_called()
        mock_get_inspectors.assert_called()
        mock_get_errors.assert_called()

        self.assertIn(fml_errors[0]["message"], result[0]["message"])
        self.assertIn(fml_errors[1]["message"], result[1]["message"])

    @patch(
        "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader._get_fml_clients",
    )
    @patch(
        "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader._get_inspectors",
    )
    def test_return_none_for_no_fml_errors(
        self,
        mock_get_clients,
        mock_get_inspectors,
    ):
        mock = MagicMock()
        mock_get_inspectors.return_value = [mock]
        mock_get_clients.return_value = [mock]
        loader = self.create_loader()
        test_blob = json.dumps({"features": {"new-feature": {"enabled": "false"}}})
        with patch(
            "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader._get_errors",
        ) as mock_get_errors:
            mock_get_errors.return_value = None
            result = loader.get_fml_errors(test_blob, "my_feature_id")

            mock_get_clients.assert_called()
            mock_get_inspectors.assert_called()
            mock_get_errors.assert_called()
            self.assertIsNone(result)

    @patch(
        "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader._get_fml_clients",
    )
    def test_return_none_for_no_fml_clients(
        self,
        mock_get_clients,
    ):
        mock_get_clients.return_value = None
        loader = self.create_loader()
        test_blob = json.dumps({"features": {"new-feature": {"enabled": "false"}}})
        result = loader.get_fml_errors(test_blob, "my_feature_id")
        self.assertIsNone(result)
