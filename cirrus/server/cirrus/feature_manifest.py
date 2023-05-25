from typing import Any, Dict, List


class FeatureManifestLanguage:
    def compute_feature_configurations(
        self,
        enrolled_partial_configuration: Dict[str, Any],
        feature_configurations: List[Dict[str, Any]],
    ) -> Dict[str, str]:
        return {"feature": "test"}


fml = FeatureManifestLanguage()
