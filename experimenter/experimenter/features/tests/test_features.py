import json

from django.test import TestCase
from mozilla_nimbus_schemas.experimenter_apis.experiments.feature_manifests import (
    DesktopFeature,
    DesktopFeatureVariable,
    FeatureVariableType,
    SdkFeature,
    SdkFeatureVariable,
)

from experimenter.experiments.models import NimbusExperiment
from experimenter.features import (
    Feature,
    Features,
)
from experimenter.features.tests import (
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
                model=DesktopFeature.parse_obj(
                    {
                        "owner": "owner@example.com",
                        "description": "Some Firefox Feature",
                        "hasExposure": True,
                        "exposureDescription": "An exposure event",
                        "isEarlyStartup": True,
                        "allowCoenrollment": True,
                        "variables": {
                            "stringEnumProperty": DesktopFeatureVariable(
                                description="String Property",
                                enum=["v1", "v2"],
                                fallbackPref="browser.somePref",
                                type=FeatureVariableType.STRING,
                            ),
                            "boolProperty": DesktopFeatureVariable(
                                description="Boolean Property",
                                type="boolean",
                            ),
                            "intProperty": DesktopFeatureVariable(
                                description="Integer Property",
                                enum=[1, 2, 3],
                                type="int",
                            ),
                            "jsonProperty": DesktopFeatureVariable(
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
                model=SdkFeature.parse_obj(
                    {
                        "description": "Default Android Browser",
                        "hasExposure": False,
                        "isEarlyStartup": None,
                        "variables": {
                            "default": SdkFeatureVariable(
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
                model=DesktopFeature.parse_obj(
                    {
                        "description": "Some Firefox Feature",
                        "owner": "owner@example.com",
                        "exposureDescription": "An exposure event",
                        "hasExposure": True,
                        "isEarlyStartup": True,
                        "allowCoenrollment": True,
                        "variables": {
                            "stringEnumProperty": DesktopFeatureVariable(
                                description="String Property",
                                enum=["v1", "v2"],
                                fallbackPref="browser.somePref",
                                type=FeatureVariableType.STRING,
                            ),
                            "boolProperty": DesktopFeatureVariable(
                                description="Boolean Property",
                                type="boolean",
                            ),
                            "intProperty": DesktopFeatureVariable(
                                description="Integer Property",
                                type="int",
                                enum=[1, 2, 3],
                            ),
                            "jsonProperty": DesktopFeatureVariable(
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


class TestValidateFeatureManifests(TestCase):
    def test_valid_feature_manifest_for_application(self):
        Features.clear_cache()
        Features.all()
