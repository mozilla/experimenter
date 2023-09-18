import os

import yaml
from packaging import version

from experimenter.settings import BASE_DIR

from rust_fml import FmlClient


class NimbusFmlLoader:
    __base_path = os.path.join(BASE_DIR, "features", "manifests", "apps.yaml")
    __major_release = "major_release_branch"
    __minor_release = "minor_release_tag"

    def __init__(self, application: str, channel: str):
        self.application: str = application
        self.channel: str = channel

    @staticmethod
    def parse_version(version_str: str):
        return version.parse(version_str)

    def create(self, path: str, channel: str) -> FmlClient:
        return FmlClient.new_with_ref(
            "@mozilla-mobile/firefox-android/fenix/app/nimbus.fml.yaml", "release", "main"
        )

    @staticmethod
    def load_yaml(file):
        return yaml.load(file.read(), Loader=yaml.Loader)

    def get_repo_location(self, file_location=__base_path):
        if os.path.exists(file_location):
            with open(file_location) as application_yaml_file:
                application_data = self.load_yaml(application_yaml_file)
                for feature_slug in application_data:
                    if feature_slug in self.application:
                        return application_data[feature_slug]["repo"]

    def get_fm_path(self, file_location=__base_path):
        if os.path.exists(file_location):
            with open(file_location) as application_yaml_file:
                application_data = self.load_yaml(application_yaml_file)
                for feature_slug in application_data:
                    if feature_slug in self.application:
                        return application_data[feature_slug]["fml_path"]

    def get_manifest_paths(self, versions: list[str]):
        manifest_paths = []
        for v in versions:
            version = self.parse_version(v)
            if os.path.exists(self.__base_path):
                with open(self.__base_path) as application_yaml_file:
                    application_data = self.load_yaml(application_yaml_file)

                    for feature_slug in application_data:
                        if feature_slug in self.application:
                            # Todo: this can be expanded later to fetch both the
                            # branch/major version and the tagged minor version.
                            manifest_path_minor = self.get_minor_release_path(
                                version, application_data, feature_slug
                            )
                            manifest_paths.append(manifest_path_minor)
                            break
        return manifest_paths

    def get_major_release_path(self, version, application_data, feature_slug):
        return application_data[feature_slug][self.__major_release].format(
            major=version.major
        )

    def get_minor_release_path(self, version, application_data, feature_slug):
        return application_data[feature_slug][self.__minor_release].format(
            major=version.major,
            minor=version.minor,
            patch=version.micro,
        )
