from ..cirrus.manifest_loader import ManifestLoader


def test_get_latest_feature_manifest_empty():
    manifest_loader = ManifestLoader()
    assert manifest_loader.get_latest_feature_manifest() == []


def test_update_feature_manifest():
    manifest_loader = ManifestLoader()
    new_manifest = [{"feature1": True}, {"feature2": False}]
    manifest_loader.update_feature_manifest(new_manifest)
    assert manifest_loader.get_latest_feature_manifest() == new_manifest
