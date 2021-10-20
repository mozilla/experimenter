import json

from django.core.checks import Error
from django.test import TestCase

from experimenter.experiments.constants import NimbusConstants
from experimenter.features import (
    Feature,
    Features,
    FeatureVariable,
    FeatureVariableType,
    check_features,
)
from experimenter.features.tests import mock_invalid_features, mock_valid_features


@mock_valid_features
class TestFeatures(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Features.clear_cache()

    def test_load_all_features(self):
        features = Features.all()
        self.assertEqual(len(features), 2)
        self.assertIn(
            Feature(
                applicationSlug="firefox-desktop",
                description="Firefox Reader Mode",
                exposureDescription="An exposure event",
                isEarlyStartup=True,
                slug="readerMode",
                variables={
                    "pocketCTAVersion": FeatureVariable(
                        description=(
                            "What version of Pocket CTA to show in Reader Mode "
                            "(Empty string is no CTA)"
                        ),
                        enum=["v1", "v2"],
                        fallbackPref="reader.pocket.ctaVersion",
                        type=FeatureVariableType.STRING,
                    )
                },
            ),
            features,
        )

        self.assertIn(
            Feature(
                applicationSlug="fenix",
                description="Default Android Browser",
                exposureDescription=False,
                isEarlyStartup=None,
                slug="defaultBrowser",
                variables={
                    "default": FeatureVariable(
                        description="Default browser setting",
                        fallbackPref=None,
                        type=FeatureVariableType.BOOLEAN,
                    )
                },
            ),
            features,
        )

    def test_load_features_by_application(self):
        desktop_features = Features.by_application(NimbusConstants.Application.DESKTOP)
        self.assertEqual(len(desktop_features), 1)
        self.assertIn(
            Feature(
                applicationSlug="firefox-desktop",
                description="Firefox Reader Mode",
                exposureDescription="An exposure event",
                isEarlyStartup=True,
                slug="readerMode",
                variables={
                    "pocketCTAVersion": FeatureVariable(
                        description=(
                            "What version of Pocket CTA to show in Reader Mode "
                            "(Empty string is no CTA)"
                        ),
                        enum=["v1", "v2"],
                        fallbackPref="reader.pocket.ctaVersion",
                        type=FeatureVariableType.STRING,
                    )
                },
            ),
            desktop_features,
        )

    def test_feature_generates_schema(self):
        desktop_feature = Features.by_application(NimbusConstants.Application.DESKTOP)[0]
        self.assertEqual(
            json.loads(desktop_feature.schema),
            {
                "additionalProperties": True,
                "properties": {
                    "pocketCTAVersion": {
                        "description": (
                            "What version of Pocket "
                            "CTA to show in Reader "
                            "Mode (Empty string is no "
                            "CTA)"
                        ),
                        "type": "string",
                        "enum": ["v1", "v2"],
                    }
                },
                "type": "object",
            },
        )


class TestCheckFeatures(TestCase):
    def setUp(self):
        Features.clear_cache()

    @mock_valid_features
    def test_valid_features_do_not_trigger_check_error(self):
        errors = check_features(None)
        self.assertEqual(errors, [])

    @mock_invalid_features
    def test_invalid_features_do_trigger_check_error(self):
        errors = check_features(None)
        self.assertEqual(
            errors,
            [
                Error(
                    msg=(
                        "Error loading feature data 1 validation error for "
                        "Feature\nvariables -> fallbackPref\n  value is "
                        "not a valid dict (type=type_error.dict)"
                    )
                )
            ],
        )
