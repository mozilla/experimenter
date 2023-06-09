import json
from typing import Any, Dict
import logging

from fml_sdk import FmlClient  # type: ignore

from .settings import channel, fml_path

logger = logging.getLogger(__name__)


class FeatureManifestLanguage:
    def __init__(self):
        self.fml_client = FmlClient(fml_path, channel)
        self.merge_errors = []

    def compute_feature_configurations(
        self,
        enrolled_partial_configuration: Dict[str, Any],
    ) -> Dict[str, Any]:
        feature_configs = {
            key: value["feature"]["value"]
            for key, value in enrolled_partial_configuration[
                "enrolledFeatureConfigMap"  # slug, featureid, value,
            ].items()
        }
        merged_res: Dict[str, Any] = self.fml_client.merge(  # type: ignore
            feature_configs
        )
        self.merge_errors = merged_res.errors
        if self.merge_errors:
            logger.error(
                f"An error occurred during enrolled partial config and FML: {self.merge_errors}"
            )

        return json.loads(merged_res.json)


fml = FeatureManifestLanguage()
