import unittest

from ..cirrus.feature_manifest import FeatureManifestLanguage


class FeatureManifestLanguageTestCase(unittest.TestCase):
    def test_compute_feature_configurations(self):
        # Create instance of FeatureManifestLanguage class
        fml = FeatureManifestLanguage()

        # Create test input data
        enrolled_partial_configuration = [
            {"id": 1, "name": "test1", "value": "true"},
            {"id": 2, "name": "test2", "value": "false"},
        ]
        feature_configurations = [
            {"id": 1, "name": "feature1", "value": "true"},
            {"id": 2, "name": "feature2", "value": "false"},
        ]

        # Call method with test input data
        result = fml.compute_feature_configurations(
            enrolled_partial_configuration, feature_configurations
        )

        # Verify that method returns expected output
        self.assertEqual(result, {"feature": "test"})
