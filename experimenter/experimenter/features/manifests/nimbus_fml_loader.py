import os
from pathlib import Path

import yaml
from packaging import version as version_packaging
from rust_fml import FmlClient

from experimenter.settings import BASE_DIR


class NimbusFmlLoader:
    BASE_PATH = Path(BASE_DIR) / "features" / "manifests" / "apps.yaml"

    def __init__(self, application: str, channel: str, file_location=BASE_PATH):
        self.application: str = application
        self.channel: str = channel
        self.application_data = self.get_application_data(application, file_location)

    def get_fml_clients(self, versions: list[str]) -> list[FmlClient]:
        if not self.application_data:
            return None
        refs = self.get_version_refs(versions)
        file_path = self.get_file_path()
        return [self.create_client(file_path, self.channel, r) for r in refs]

    @staticmethod
    def get_application_data(application_name, file_location=BASE_PATH):
        if os.path.exists(file_location):
            with open(file_location) as application_yaml_file:
                file = yaml.safe_load(application_yaml_file.read())
                if application_name in file:
                    return file[application_name]
                else:
                    return None

    def get_file_path(self):
        if not self.application_data:
            return None
        return Path(self.application_data["repo"]) / self.application_data["fml_path"]

    def get_version_refs(self, versions):
        if versions == []:
            return ["main"]
        refs = []
        for v in versions:
            version = version_packaging.parse(v)
            # Todo: this can be expanded later to fetch both the
            # branch/major version and the tagged minor version.
            version_ref_minor = self.get_minor_version_ref(
                version,
            )
            refs.append(version_ref_minor)
        return refs

    def get_major_version_ref(self, version):
        if not self.application_data:
            return None
        return self.application_data["major_release_branch"].format(
            major=version.major,
        )

    def get_minor_version_ref(self, version):
        if not self.application_data:
            return None
        return self.application_data["minor_release_tag"].format(
            major=version.major,
            minor=version.minor,
            patch=version.micro,
        )

    def create_client(self, path: str, channel: str, ref: str) -> FmlClient:
        return FmlClient.new_with_ref(path, channel, ref)
