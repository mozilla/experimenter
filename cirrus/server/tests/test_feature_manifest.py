import unittest

from ..cirrus.feature_manifest import FeatureManifestLanguage


class FeatureManifestLanguageTestCase(unittest.TestCase):
    def test_compute_feature_configurations(self):
        fml = FeatureManifestLanguage()

        enrolled_partial_configuration = [
            {"id": 1, "name": "test1", "value": "true"},
            {"id": 2, "name": "test2", "value": "false"},
        ]
        feature_configurations = [
            {"id": 1, "name": "feature1", "value": "true"},
            {"id": 2, "name": "feature2", "value": "false"},
        ]

        result = fml.compute_feature_configurations(
            enrolled_partial_configuration, feature_configurations
        )

        self.assertEqual(result, {"feature": "test"})
