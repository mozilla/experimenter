import logging
from pathlib import Path

import yaml
from rust_fml import FmlClient, FmlFeatureInspector

from experimenter.experiments.constants import NimbusConstants
from experimenter.settings import BASE_DIR

logger = logging.getLogger()


class NimbusFmlLoader:
    BASE_PATH = Path(BASE_DIR, "features", "manifests", "apps.yaml")
    MANIFEST_PATH = Path(BASE_DIR, "features", "manifests")

    def __init__(self, application: str, channel: str, file_location=BASE_PATH):
        self.application: str = (
            application if application in NimbusConstants.Application else None
        )
        self.channel: str = channel if channel in NimbusConstants.Channel else None
        self.application_data = self._get_application_data(application, file_location)

    @staticmethod
    def _get_application_data(application_name, file_location=BASE_PATH):
        """Fetch app data from local apps.yaml file to find application names, github
        repos, fml paths within the repos, and release versions.
        """
        if Path.exists(file_location):
            with open(file_location) as application_yaml_file:
                file = yaml.safe_load(application_yaml_file.read())
                if application_name in file:
                    return file[application_name]
                else:
                    return None

    def _get_local_file_path(self):
        """Get path to release feature manifest from experimenter (local)."""
        if self.application is not None:
            path = Path(self.MANIFEST_PATH, self.application, f"{self.channel}.fml.yaml")
            if Path.exists(path):
                return path
        else:
            logger.error(
                "Nimbus FML Loader: Invalid application. Failed to get local "
                "feature manifest."
            )
        return None

    # Todo: Add versioning https://mozilla-hub.atlassian.net/browse/EXP-3875
    def _get_fml_clients(self, versions: list[str]) -> list[FmlClient]:
        clients = []
        if file_path := self._get_local_file_path():
            client = self._create_client(str(file_path), self.channel)
            if client is not None:
                clients.append(client)
            else:
                logger.error(
                    "Nimbus FML Loader: "
                    f"Failed to create FML clients for file path {file_path} and "
                    f"channel {self.channel}."
                )
        return clients

    def _create_client(self, path: str, channel: str) -> FmlClient:
        return FmlClient(path, channel)

    def _get_inspectors(
        self, clients: list[FmlClient], feature_id: str
    ) -> list[FmlFeatureInspector]:
        return [
            inspector
            for inspector in (
                client.get_feature_inspector(feature_id) for client in clients
            )
            if inspector is not None
        ]

    @staticmethod
    def _get_errors(inspector: FmlFeatureInspector, blob: str):
        return inspector.get_errors(blob)

    # Todo: Add versioning https://mozilla-hub.atlassian.net/browse/EXP-3875
    def get_fml_errors(self, blob: str, feature_id: str):
        """Fetch errors from the FML. This method creates FML clients, which are
        used by `FmlFeatureInspector`s to fetch errors based on the blob of text and
        the given feature.

        Returns:
            A list of feature manifest errors.
        """
        if self.application is not None:
            errors = []
            if clients := self._get_fml_clients([]):
                if inspectors := self._get_inspectors(clients, feature_id):
                    if inspectors != []:
                        for inspector in inspectors:
                            if error := self._get_errors(inspector, blob):
                                errors.extend(error)
            return errors
        else:
            logger.error(
                "Nimbus FML Loader: Invalid application. Failed to fetch FML errors."
            )
            return []
