import logging
from pathlib import Path

import yaml
from packaging import version as version_packaging
from rust_fml import FmlClient, FmlFeatureInspector

from experimenter.settings import BASE_DIR

logger = logging.getLogger()


class NimbusFmlLoader:
    BASE_PATH = Path(BASE_DIR) / "features" / "manifests" / "apps.yaml"
    MANIFEST_PATH = Path(BASE_DIR) / "features" / "manifests"

    def __init__(self, application: str, channel: str, file_location=BASE_PATH):
        self.application: str = application
        self.channel: str = channel
        self.application_data = self._get_application_data(application, file_location)

    @staticmethod
    def _get_application_data(application_name, file_location=BASE_PATH):
        """
        Fetch app data from local apps.yaml file to find application
        names, github repos, fml paths within the repos, and release
        versions.
        """
        if Path.exists(file_location):
            with open(file_location) as application_yaml_file:
                file = yaml.safe_load(application_yaml_file.read())
                if application_name in file:
                    return file[application_name]
                else:
                    return None

    def _get_local_file_path(self):
        """
        Get path to release feature manifest from experimenter (local).
        """
        path = Path(self.MANIFEST_PATH) / f"{self.application}" / "release.fml.yaml"
        if Path.exists(path):
            return path

    def _get_remote_file_path(self):
        """
        Get path to the feature manifest from location defined in apps.yaml.
        """
        if not self.application_data:
            return None
        return (
            Path(self.application_data["repo"]["name"])
            / self.application_data["fml_path"]
        )

    # Todo: Add versioning https://mozilla-hub.atlassian.net/browse/EXP-3875
    def _get_version_refs(self, versions):
        """
        Get github refs for each version.
        """
        if versions == []:
            return ["main"]
        refs = []
        for v in versions:
            version = version_packaging.parse(v)
            # Todo: this can be expanded later to fetch both the
            # branch/major version and the tagged minor version.
            version_ref_minor = self._get_minor_version_ref(
                version,
            )
            refs.append(version_ref_minor)
        return refs

    def _get_major_version_ref(self, version):
        if not self.application_data:
            return None
        return self.application_data["major_release_branch"].format(
            major=version.major,
        )

    def _get_minor_version_ref(self, version):
        if not self.application_data:
            return None
        return self.application_data["minor_release_tag"].format(
            major=version.major,
            minor=version.minor,
            patch=version.micro,
        )

    # Todo: Add versioning https://mozilla-hub.atlassian.net/browse/EXP-3875
    def _get_fml_clients(self, versions: list[str]) -> list[FmlClient]:
        refs = self._get_version_refs(versions)
        file_path = self._get_local_file_path()
        clients = []
        for r in refs:
            client = self._create_client(str(file_path), self.channel)
            if client is not None:
                clients.append(client)
            else:
                logger.info(
                    "Nimbus FML Loader: "
                    f"Failed to create FML clients for file path {file_path}, "
                    f"channel {self.channel}, and ref {r}."
                )
        return clients

    def _create_client(self, path: str, channel: str) -> FmlClient:
        return FmlClient(path, channel)

    def _get_inspectors(
        self, clients: list[FmlClient], feature_id: str
    ) -> list[FmlFeatureInspector]:  # pragma: no cover
        return [client.get_feature_inspector(feature_id) for client in clients]

    def _get_errors(self, inspector: FmlFeatureInspector, blob: str):
        return inspector.get_errors(blob)  # pragma: no cover

    # Todo: Add versioning https://mozilla-hub.atlassian.net/browse/EXP-3875
    def get_fml_errors(self, blob: str, feature_id: str):
        """
        Fetch errors from the FML. This method creates FML clients, which are used by
        `FmlFeatureInspector`s to fetch errors based on the blob of text and the
        given feature.

        returns A list of feature manifest errors.
        """
        if clients := self._get_fml_clients([]):
            if inspectors := self._get_inspectors(clients, feature_id):
                errors = []
                if inspectors != [None]:
                    for inspector in inspectors:
                        error = self._get_errors(inspector, blob)
                        if error is not None:
                            errors.extend(error)
                        else:
                            return None
                return errors
        return None
