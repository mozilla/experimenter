import unittest

from cirrus.feature_manifest import FeatureManifestLanguage


class FeatureManifestLanguageTestCase(unittest.TestCase):
    def test_compute_feature_configurations(self):
        fml = FeatureManifestLanguage()

        enrolled_partial_configuration = {
            "enrolledFeatureConfigMap": {},
            "enrollments": [],
            "events": [],
        }

        result = fml.compute_feature_configurations(enrolled_partial_configuration)

        self.assertEqual(
            result, {"example-feature": {"enabled": False, "something": "wicked"}}
        )
