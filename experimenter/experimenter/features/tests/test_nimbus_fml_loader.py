import os

from django.test import TestCase

from experimenter.features.manifests.nimbus_fml_loader import NimbusFmlLoader
from experimenter.settings import BASE_DIR


class TestNimbusFmlLoader(TestCase):
    @staticmethod
    def create_loader(
        application: str = "fenix",
        channel: str = "production",
    ):
        return NimbusFmlLoader(application, channel)

    def test_intiate_new_fml_loader(self):
        application = "firefox_ios"
        channel = "production"

        loader = NimbusFmlLoader(application, channel)

        self.assertEqual(loader.application, application)
        self.assertEqual(loader.channel, channel)

    def test_parse_versions(self):
        version = "112.1.0"
        parse = NimbusFmlLoader.parse_version(version)
        self.assertEqual(str(parse), version)
        self.assertEqual(parse.major, 112)
        self.assertEqual(parse.minor, 1)
        self.assertEqual(parse.micro, 0)

    def test_load_yaml(self):
        path = os.path.join(BASE_DIR, "features", "tests", "test.yaml")
        loader = self.create_loader()

        if os.path.exists(path):
            with open(path) as file:
                yaml = loader.load_yaml(file)
                self.assertIsNotNone(yaml)

    def test_get_repo_location(self):
        path = os.path.join(BASE_DIR, "features", "tests", "test.yaml")
        expected = r"\@mozilla-mobile/firefox-android"

        loader = self.create_loader()
        result = loader.get_repo_location(path)
        self.assertEqual(result, expected)

    def test_get_fm_path(self):
        path = os.path.join(BASE_DIR, "features", "tests", "test.yaml")
        expected = "fenix/app/nimbus.fml.yaml"

        loader = self.create_loader()
        result = loader.get_fm_path(path)
        self.assertEqual(result, expected)

    def test_fetch_single_manifest_version(self):
        application = "firefox_ios"
        channel = "release"
        version = ["112.1.0"]

        client = self.create_loader(application, channel)
        manifests = client.get_manifest_paths(version)

        self.assertEqual(client.application, application)
        self.assertEqual(client.channel, channel)
        self.assertEqual(len(manifests), 1)

    def test_fetch_multiple_manifest_versions(self):
        application = "firefox_ios"
        channel = "release"
        versions = [
            "112.1.0",
            "112.1.1",
            "113.0.0",
            "118.7.3",
        ]

        client = self.create_loader(application, channel)
        manifests = client.get_manifest_paths(versions)

        self.assertEqual(client.application, application)
        self.assertEqual(client.channel, channel)
        self.assertEqual(len(manifests), 4)

    def test_get_major_version_fml_paths(self):
        path = os.path.join(BASE_DIR, "features", "tests", "test.yaml")
        loader = self.create_loader()
        version = loader.parse_version("112.1.0")
        expected = "releases_v112"

        if os.path.exists(path):
            with open(path) as application_yaml_file:
                application_data = loader.load_yaml(application_yaml_file)
                result = loader.get_major_release_path(
                    version,
                    application_data,
                    "fenix",
                )
                self.assertEqual(result, expected)

    def test_get_minor_version_fml_paths(self):
        path = os.path.join(BASE_DIR, "features", "tests", "test.yaml")
        loader = self.create_loader()
        version = loader.parse_version("112.1.0")
        expected = "fenix-v112.1.0"

        if os.path.exists(path):
            with open(path) as application_yaml_file:
                application_data = loader.load_yaml(application_yaml_file)
                result = loader.get_minor_release_path(
                    version,
                    application_data,
                    "fenix",
                )

                self.assertEqual(result, expected)

    def test_create(self):
        loader = self.create_loader()
        fml_path = "fenix/app/nimbus.fml.yaml"
        release_version = "v112.1.0"

        result = loader.create(fml_path, release_version, loader.channel)
        self.assertIsNotNone(result)
