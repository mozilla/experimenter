from pathlib import Path
from unittest import mock

from django.test import TestCase
from packaging import version

from experimenter.features.manifests.nimbus_fml_loader import NimbusFmlLoader
from experimenter.settings import BASE_DIR


class TestNimbusFmlLoader(TestCase):
    TEST_BASE_PATH = Path(BASE_DIR) / "features" / "tests" / "test.yaml"

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
        expected_repo = r"\@mozilla-mobile/firefox-android"

        loader = NimbusFmlLoader(application, channel, self.TEST_BASE_PATH)

        self.assertEqual(loader.application, application)
        self.assertEqual(loader.channel, channel)
        self.assertEqual(loader.application_data["repo"], expected_repo)

    def test_get_application_data_from_file(self):
        application = "fenix"
        expected_repo = r"\@mozilla-mobile/firefox-android"
        expected_fml = "fenix/app/nimbus.fml.yaml"

        data = NimbusFmlLoader.get_application_data(
            application_name=application, file_location=self.TEST_BASE_PATH
        )
        self.assertEqual(data["repo"], expected_repo)
        self.assertEqual(data["fml_path"], expected_fml)

    def test_get_application_data_does_not_exist(self):
        application = "garfield"

        data = NimbusFmlLoader.get_application_data(
            application_name=application, file_location=self.TEST_BASE_PATH
        )
        self.assertIsNone(data)

    def test_get_application_path_does_not_exist(self):
        application = "garfield"
        path = Path(BASE_DIR) / "features" / "garfield" / "bingo.yaml"

        data = NimbusFmlLoader.get_application_data(
            application_name=application, file_location=path
        )
        self.assertIsNone(data)

    def test_get_ref_no_versions(self):
        application = "fenix"
        channel = "release"
        no_version = []

        client = self.create_loader()
        refs = client.get_version_refs(no_version)

        self.assertEqual(client.application, application)
        self.assertEqual(client.channel, channel)
        self.assertEqual(refs, ["main"])

    def test_get_ref_for_single_version(self):
        application = "fenix"
        channel = "release"
        version = ["112.1.0"]

        client = self.create_loader()
        refs = client.get_version_refs(version)

        self.assertEqual(client.application, application)
        self.assertEqual(client.channel, channel)
        self.assertEqual(len(refs), 1)

    def test_get_refs_for_multiple_versions(self):
        application = "fenix"
        channel = "release"
        expected_repo = r"\@mozilla-mobile/firefox-android"
        versions = [
            "112.1.0",
            "112.1.1",
            "113.0.0",
            "118.7.3",
        ]

        client = self.create_loader()
        self.assertEqual(client.application_data["repo"], expected_repo)

        refs = client.get_version_refs(versions)

        self.assertEqual(client.application, application)
        self.assertEqual(client.channel, channel)
        self.assertEqual(len(refs), 4)

    def test_get_major_version_refs(self):
        loader = self.create_loader()
        v = version.parse("112.1.0")
        expected = "releases_v112"

        result = loader.get_major_version_ref(v)
        self.assertEqual(result, expected)

    def test_get_minor_version_refs(self):
        loader = self.create_loader()
        v = version.parse("112.1.0")
        expected = "fenix-v112.1.0"

        result = loader.get_minor_version_ref(v)
        self.assertEqual(result, expected)

    def test_get_major_version_refs_application_is_none(self):
        v = version.parse("112.1.0")
        loader = self.create_loader()
        loader.application_data = None
        result = loader.get_major_version_ref(version=v)
        self.assertIsNone(result)

    def test_get_minor_version_refs_application_is_none(self):
        v = version.parse("112.1.0")
        loader = self.create_loader()
        loader.application_data = None
        result = loader.get_minor_version_ref(version=v)
        self.assertIsNone(result)

    def test_get_fml_clients(self):
        versions = [
            "112.1.0",
            "112.1.1",
            "113.0.0",
            "118.7.3",
        ]
        loader = self.create_loader()

        with mock.patch(
            "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader.create_client",
        ) as create:
            result = loader.get_fml_clients(versions)
            self.assertEqual(len(result), 4)
            create.assert_called()

    def test_get_fml_client_no_versions(self):
        no_version = []
        loader = self.create_loader()
        path = Path(r"\@mozilla-mobile/firefox-android/fenix/app/nimbus.fml.yaml")
        with mock.patch(
            "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader.create_client",
        ) as create:
            result = loader.get_fml_clients(no_version)
            self.assertEqual(len(result), 1)
            create.assert_called()
            create.assert_called_with(path, "release", "main")

    def test_get_fml_client_no_app_config(self):
        loader = self.create_loader()
        loader.application = None
        loader.channel = None
        loader.application_data = None

        with mock.patch(
            "rust_fml.FmlClient.new_with_ref",
        ) as new_with_ref:
            result = loader.get_fml_clients(versions=[])
            self.assertIsNone(result)
            new_with_ref.assert_not_called()

    def test_create_fml_client(self):
        application = "fenix"
        path = r"\@mozilla-mobile/firefox-android/fenix/app/nimbus.fml.yaml"
        ref = "fenix-v120.2.1"
        channel = "release"
        loader = self.create_loader(application, channel)

        with mock.patch(
            "rust_fml.FmlClient.new_with_ref",
        ) as new_with_ref:
            loader.create_client(path, channel, ref)
            new_with_ref.assert_called()

    def test_get_file_path(self):
        expected_path = Path(
            r"\@mozilla-mobile/firefox-android/fenix/app/nimbus.fml.yaml",
        )
        loader = self.create_loader()
        file_path = loader.get_file_path()
        self.assertEqual(file_path, expected_path)

    def test_get_file_path_no_application_data(self):
        loader = self.create_loader()
        loader.application_data = None
        file_path = loader.get_file_path()
        self.assertIsNone(file_path)
