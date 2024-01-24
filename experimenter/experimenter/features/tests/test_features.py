import json

from django.core.checks import Error
from django.test import TestCase
from mozilla_nimbus_schemas.experiments.feature_manifests import (
    FeatureVariable,
    FeatureVariableType,
    FeatureWithExposure,
    FeatureWithoutExposure,
)

from experimenter.experiments.models import NimbusExperiment
from experimenter.features import (
    Feature,
    Features,
    check_features,
)
from experimenter.features.tests import (
    mock_invalid_features,
    mock_invalid_remote_schema_features,
    mock_remote_schema_features,
    mock_valid_features,
)


@mock_valid_features
class TestFeatures(TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Features.clear_cache()

    def test_load_all_features(self):
        features = Features.all()
        self.assertEqual(len(features), 5)
        self.assertIn(
            Feature(
                slug="someFeature",
                application_slug="firefox-desktop",
                model=FeatureWithExposure.parse_obj(
                    {
                        "description": "Some Firefox Feature",
                        "hasExposure": True,
                        "exposureDescription": "An exposure event",
                        "isEarlyStartup": True,
                        "variables": {
                            "stringEnumProperty": FeatureVariable(
                                description="String Property",
                                enum=["v1", "v2"],
                                fallbackPref="browser.somePref",
                                type=FeatureVariableType.STRING,
                            ),
                            "boolProperty": FeatureVariable(
                                description="Boolean Property",
                                type="boolean",
                            ),
                            "intProperty": FeatureVariable(
                                description="Integer Property",
                                enum=[1, 2, 3],
                                type="int",
                            ),
                            "jsonProperty": FeatureVariable(
                                description="Arbitrary JSON Property",
                                type="json",
                            ),
                        },
                    }
                ),
            ),
            features,
        )

        self.assertIn(
            Feature(
                slug="defaultBrowser",
                application_slug="fenix",
                model=FeatureWithoutExposure.parse_obj(
                    {
                        "description": "Default Android Browser",
                        "hasExposure": False,
                        "isEarlyStartup": None,
                        "variables": {
                            "default": FeatureVariable(
                                description="Default browser setting",
                                fallbackPref=None,
                                type=FeatureVariableType.BOOLEAN,
                            )
                        },
                    }
                ),
            ),
            features,
        )

    def test_load_features_by_application(self):
        desktop_features = Features.by_application(NimbusExperiment.Application.DESKTOP)
        self.assertEqual(len(desktop_features), 4)
        self.assertIn(
            Feature(
                slug="someFeature",
                application_slug="firefox-desktop",
                model=FeatureWithExposure.parse_obj(
                    {
                        "description": "Some Firefox Feature",
                        "exposureDescription": "An exposure event",
                        "hasExposure": True,
                        "isEarlyStartup": True,
                        "variables": {
                            "stringEnumProperty": FeatureVariable(
                                description="String Property",
                                enum=["v1", "v2"],
                                fallbackPref="browser.somePref",
                                type=FeatureVariableType.STRING,
                            ),
                            "boolProperty": FeatureVariable(
                                description="Boolean Property",
                                type="boolean",
                            ),
                            "intProperty": FeatureVariable(
                                description="Integer Property",
                                type="int",
                                enum=[1, 2, 3],
                            ),
                            "jsonProperty": FeatureVariable(
                                description="Arbitrary JSON Property",
                                type="json",
                            ),
                        },
                    }
                ),
            ),
            desktop_features,
        )

    def test_feature_generates_schema(self):
        desktop_feature = Features.by_application(NimbusExperiment.Application.DESKTOP)[0]
        self.assertEqual(
            json.loads(desktop_feature.get_jsonschema()),
            {
                "type": "object",
                "properties": {
                    "stringEnumProperty": {
                        "description": "String Property",
                        "type": "string",
                        "enum": ["v1", "v2"],
                    },
                    "boolProperty": {
                        "description": "Boolean Property",
                        "type": "boolean",
                    },
                    "intProperty": {
                        "description": "Integer Property",
                        "type": "integer",
                        "enum": [1, 2, 3],
                    },
                    "jsonProperty": {"description": "Arbitrary JSON Property"},
                },
                "additionalProperties": False,
            },
        )


class TestRemoteSchemaFeatures(TestCase):
    def setUp(self):
        Features.clear_cache()

    @mock_remote_schema_features
    def test_loads_remote_schema(self):
        desktop_feature = Features.by_application(NimbusExperiment.Application.DESKTOP)[0]
        remote_schema = desktop_feature.get_jsonschema()
        self.assertEqual(json.loads(remote_schema), {"schema": True})

    @mock_invalid_remote_schema_features
    def test_returns_none_for_invalid_json(self):
        desktop_feature = Features.by_application(NimbusExperiment.Application.DESKTOP)[0]
        self.assertIsNone(desktop_feature.get_jsonschema())


class TestCheckFeatures(TestCase):
    maxDiff = None

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
                        "FeatureManifest\n__root__ -> readerMode -> __root__ -> "
                        "FeatureWithoutExposure -> variables -> fallbackPref\n"
                        "  value is not a valid dict (type=type_error.dict)"
                    )
                )
            ],
        )
