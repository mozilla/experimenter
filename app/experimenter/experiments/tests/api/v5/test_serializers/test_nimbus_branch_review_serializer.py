from django.test import TestCase

from experimenter.experiments.api.v5.serializers import NimbusBranchReviewSerializer
from experimenter.experiments.tests.factories.nimbus import NimbusFeatureConfigFactory


class TestNimbusBranchReviewSerializer(TestCase):
    maxDiff = None

    BASIC_JSON_SCHEMA = """\
    {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "description": "Password autocomplete",
    "type": "object",
    "properties": {
        "directMigrateSingleProfile": {
        "description": "Should we directly migrate a single profile?",
        "type": "boolean"
        }
    },
    "additionalProperties": false
    }
    """

    def test_branch_with_invalid_feature_value_json(self):
        feature_config = NimbusFeatureConfigFactory.create(schema=self.BASIC_JSON_SCHEMA)
        branch_data = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "feature_values": {
                "feature_config": feature_config.id,
                "enabled": True,
                "value": "invalid json",
            },
        }
        branch_serializer = NimbusBranchReviewSerializer(data=branch_data)
        self.assertFalse(branch_serializer.is_valid())
        self.assertIn("feature_values", branch_serializer.errors)
