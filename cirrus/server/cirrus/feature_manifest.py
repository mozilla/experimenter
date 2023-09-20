import json
import logging
from typing import Any, Dict, List

from fml_sdk import FmlClient, FmlError, MergedJsonWithErrors  # type: ignore

logger = logging.getLogger(__name__)


class FeatureManifestLanguage:
    def __init__(self, fml_path: str, channel: str):
        self.fml_client = FmlClient(fml_path, channel)
        self.merge_errors: List[FmlError] = []

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
        merged_res: MergedJsonWithErrors = self.fml_client.merge(  # type: ignore
            feature_configs
        )
        self.merge_errors = merged_res.errors

        if self.merge_errors:
            logger.error(
                "An error occurred during enrolled partial, "
                "config and FML: "
                f"{self.merge_errors}"
            )

        return json.loads(merged_res.json)

    def get_coenrolling_feature_ids(self) -> List[str]:
        return self.fml_client.get_coenrolling_feature_ids()
