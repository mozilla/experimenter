import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

from rust_fml import FmlClient, FmlFeatureInspector

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusFeatureVersion
from experimenter.settings import BASE_DIR

logger = logging.getLogger()


class NimbusFmlLoader:
    MANIFEST_PATH = Path(BASE_DIR, "features", "manifests")

    def __init__(self, application: str, channel: str):
        self.application: str = (
            application if application in NimbusConstants.Application else None
        )
        self.channel: str = channel if channel in NimbusConstants.Channel else None

    @classmethod
    @lru_cache
    def create_loader(cls, application: str, channel: str):
        """Application and channel should stay the same for each iteration of the
        FML loader.
        """
        return cls(application, channel)

    def file_path(self, version: NimbusFeatureVersion = None):
        """Get path to release feature manifest from experimenter (local)."""

        if self.application is not None:
            path = Path(self.MANIFEST_PATH, self.application)
            if version:
                path /= f"v{version}"
            path /= f"{self.channel}.fml.yaml"

            if Path.exists(path):
                return path
            else:
                logger.error(f"Nimbus FML Loader: Invalid manifest path: {path}")
                return None
        else:
            logger.error(
                "Nimbus FML Loader: Invalid application. Failed to get local "
                "feature manifest."
            )
        return None

    @lru_cache  # noqa: B019
    def fml_client(self, version: Optional[NimbusFeatureVersion] = None) -> FmlClient:
        """There is a single FmlClient for each combination of application, app version,
        and channel.
        """
        file_path = self.file_path(version)
        if file_path is not None:
            return FmlClient(
                str(file_path),
                self.channel,
            )
        else:
            logger.error("Nimbus FML Loader: Failed to get FmlClient.")
            return None

    def feature_inspector(
        self, client: FmlClient, feature_id: str
    ) -> FmlFeatureInspector:
        """There is a single FmlFeatureInspector for each feature."""
        return client.get_feature_inspector(feature_id)

    @staticmethod
    def _get_errors(inspector: FmlFeatureInspector, blob: str):
        return inspector.get_errors(blob)

    def get_fml_errors(
        self,
        blob: str,
        feature_id: str,
        version: Optional[NimbusFeatureVersion] = None,
    ):
        """Fetch errors from the FML. This method creates FML clients, which are
        used by `FmlFeatureInspector`s to fetch FML errors based on a blob of text and
        the given feature id.

        Returns:
            A list of feature manifest errors.
        """
        if self.application is not None:
            errors = []
            if client := self.fml_client(version):
                if inspector := self.feature_inspector(client, feature_id):
                    if errs := self._get_errors(inspector, blob):
                        errors.extend(errs)
                return errors
        logger.error(
            "Nimbus FML Loader: Invalid application. Failed to fetch FML errors."
        )
        return []
