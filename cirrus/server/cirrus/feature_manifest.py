import json
from typing import Any, Dict

from fml_sdk import FmlClient  # type: ignore

from .settings import channel, fml_path


class FeatureManifestLanguage:
    def __init__(self):
        self.fml_client = FmlClient(fml_path, channel)

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
        if len(merged_res.errors) > 0:
            print(merged_res.errors)

        merged_res_json = json.loads(merged_res.json)
        print("merged res", merged_res)
        return merged_res_json


fml = FeatureManifestLanguage()
