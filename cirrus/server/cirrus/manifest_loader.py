from typing import Any, Dict, List


class ManifestLoader:
    feature_manifest: List[Dict[str, Any]] = []

    @classmethod
    def get_latest_feature_manifest(cls) -> List[Dict[str, Any]]:
        return cls.feature_manifest

    @classmethod
    def update_feature_manifest(
        cls, updated_feature_manifest: List[Dict[str, Any]]
    ) -> None:
        cls.feature_manifest = updated_feature_manifest


manifest_loader = ManifestLoader()
