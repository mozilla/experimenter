import os

import yaml
from packaging import version as Version
from rust_fml import FmlClient

from experimenter.settings import BASE_DIR


class NimbusFmlLoader:
    __base_path = os.path.join(BASE_DIR, "features", "manifests", "apps.yaml")

    def __init__(self, application: str, channel: str, file_location=__base_path):
        self.application: str = application
        self.channel: str = channel
        self.application_data = self.get_application_data(application, file_location)
        # Todo: Connect FML paths and channels https://mozilla-hub.atlassian.net/browse/EXP-3845
        self.fml_client = self.create("", "")

    @staticmethod
    def get_application_data(app, file_location=__base_path):
        if os.path.exists(file_location):
            with open(file_location) as application_yaml_file:
                file = yaml.load(application_yaml_file.read(), Loader=yaml.Loader)
                for app_name in file:
                    if app_name in app:
                        return file[app_name]

    def get_manifest_paths(self, versions: list[str]):
        manifest_paths = []
        for v in versions:
            version = Version.parse(v)
            # Todo: this can be expanded later to fetch both the
            # branch/major version and the tagged minor version.
            manifest_path_minor = self.get_minor_release_path(
                version,
            )
            manifest_paths.append(manifest_path_minor)
        return manifest_paths

    def get_major_release_path(self, version):
        if not self.application_data:
            return None
        return self.application_data["major_release_branch"].format(
            major=version.major,
        )

    def get_minor_release_path(self, version):
        if not self.application_data:
            return None
        return self.application_data["minor_release_tag"].format(
            major=version.major,
            minor=version.minor,
            patch=version.micro,
        )

    # Todo: Connect FML paths and channels https://mozilla-hub.atlassian.net/browse/EXP-3845
    def create(self, path: str, channel: str) -> FmlClient:
        return FmlClient.new_with_ref(
            "@mozilla-mobile/firefox-android/fenix/app/nimbus.fml.yaml", "release", "main"
        )
