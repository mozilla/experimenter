import os

from django.test import TestCase
from packaging import version

from experimenter.features.manifests.nimbus_fml_loader import NimbusFmlLoader
from experimenter.settings import BASE_DIR


class TestNimbusFmlLoader(TestCase):
    __base_path = os.path.join(BASE_DIR, "features", "manifests", "apps.yaml")

    @staticmethod
    def create_loader(
        application: str = "fenix",
        channel: str = "release",
        path=__base_path,
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
        path = os.path.join(BASE_DIR, "features", "tests", "test.yaml")

        loader = NimbusFmlLoader(application, channel, path)

        self.assertEqual(loader.application, application)
        self.assertEqual(loader.channel, channel)
        self.assertEqual(loader.application_data["repo"], expected_repo)
        self.assertIsNotNone(loader.fml_client)

    def test_get_application_data_from_file(self):
        application = "fenix"
        path = os.path.join(BASE_DIR, "features", "tests", "test.yaml")
        expected_repo = r"\@mozilla-mobile/firefox-android"
        expected_fml = "fenix/app/nimbus.fml.yaml"

        data = NimbusFmlLoader.get_application_data(app=application, file_location=path)
        self.assertEqual(data["repo"], expected_repo)
        self.assertEqual(data["fml_path"], expected_fml)

    def test_get_application_data_does_not_exist(self):
        application = "garfield"
        path = os.path.join(BASE_DIR, "features", "tests", "test.yaml")

        data = NimbusFmlLoader.get_application_data(app=application, file_location=path)
        self.assertIsNone(data)

    def test_get_application_path_does_not_exist(self):
        application = "garfield"
        path = os.path.join(BASE_DIR, "features", "garfield", "bingo.yaml")

        data = NimbusFmlLoader.get_application_data(app=application, file_location=path)
        self.assertIsNone(data)

    def test_fetch_single_manifest_version(self):
        application = "fenix"
        channel = "release"
        version = ["112.1.0"]

        client = self.create_loader()
        manifests = client.get_manifest_paths(version)

        self.assertEqual(client.application, application)
        self.assertEqual(client.channel, channel)
        self.assertEqual(len(manifests), 1)

    def test_fetch_multiple_manifest_versions(self):
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

        manifests = client.get_manifest_paths(versions)

        self.assertEqual(client.application, application)
        self.assertEqual(client.channel, channel)
        self.assertEqual(len(manifests), 4)

    def test_get_major_version_fml_paths(self):
        loader = self.create_loader()
        v = version.parse("112.1.0")
        expected = "releases_v112"

        result = loader.get_major_release_path(v)
        self.assertEqual(result, expected)

    def test_get_minor_version_fml_paths(self):
        loader = self.create_loader()
        v = version.parse("112.1.0")
        expected = "fenix-v112.1.0"

        result = loader.get_minor_release_path(v)
        self.assertEqual(result, expected)

    def test_get_major_version_paths_application_is_none(self):
        v = version.parse("112.1.0")
        loader = self.create_loader()
        loader.application_data = None
        result = loader.get_major_release_path(version=v)
        self.assertIsNone(result)

    def test_get_minor_version_paths_application_is_none(self):
        v = version.parse("112.1.0")
        loader = self.create_loader()
        loader.application_data = None
        result = loader.get_minor_release_path(version=v)
        self.assertIsNone(result)

    def test_create(self):
        loader = self.create_loader()
        fml_path = "fenix/app/nimbus.fml.yaml"

        result = loader.create(fml_path, loader.channel)
        self.assertIsNotNone(result)
