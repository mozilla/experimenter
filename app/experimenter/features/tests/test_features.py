import json

import mock
import requests
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
from experimenter.features.tests import (
    mock_invalid_features,
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
        self.assertEqual(len(features), 3)
        self.assertIn(
            Feature(
                applicationSlug="firefox-desktop",
                description="Some Firefox Feature",
                exposureDescription="An exposure event",
                isEarlyStartup=True,
                slug="someFeature",
                variables={
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
                    ),
                    "jsonProperty": FeatureVariable(
                        description="Arbitrary JSON Property",
                        type="json",
                    ),
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
        self.assertEqual(len(desktop_features), 2)
        self.assertIn(
            Feature(
                applicationSlug="firefox-desktop",
                description="Some Firefox Feature",
                exposureDescription="An exposure event",
                isEarlyStartup=True,
                slug="someFeature",
                variables={
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
                    ),
                    "jsonProperty": FeatureVariable(
                        description="Arbitrary JSON Property",
                        type="json",
                    ),
                },
            ),
            desktop_features,
        )

    def test_feature_generates_schema(self):
        desktop_feature = Features.by_application(NimbusConstants.Application.DESKTOP)[0]
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
                    "intProperty": {"description": "Integer Property", "type": "integer"},
                    "jsonProperty": {"description": "Arbitrary JSON Property"},
                },
                "additionalProperties": False,
            },
        )


@mock_remote_schema_features
class TestRemoteSchemaFeatures(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Features.clear_cache()

    def setup_valid_remote_schema(self):
        self.remote_schema = json.dumps({"schema": True})

        mock_requests_get_patcher = mock.patch("experimenter.features.requests.get")
        self.mock_requests_get = mock_requests_get_patcher.start()
        self.addCleanup(mock_requests_get_patcher.stop)
        mock_response = mock.MagicMock()
        mock_response.content = self.remote_schema
        self.mock_requests_get.return_value = mock_response

    def setup_request_error(self):
        self.remote_schema = json.dumps({"schema": True})

        mock_requests_get_patcher = mock.patch("experimenter.features.requests.get")
        self.mock_requests_get = mock_requests_get_patcher.start()
        self.addCleanup(mock_requests_get_patcher.stop)
        self.mock_requests_get.side_effect = requests.ConnectionError()

    def setup_json_error(self):
        self.remote_schema = "{invalid json"

        mock_requests_get_patcher = mock.patch("experimenter.features.requests.get")
        self.mock_requests_get = mock_requests_get_patcher.start()
        self.addCleanup(mock_requests_get_patcher.stop)
        mock_response = mock.MagicMock()
        mock_response.content = self.remote_schema
        self.mock_requests_get.return_value = mock_response

    def test_loads_remote_schema(self):
        self.setup_valid_remote_schema()

        desktop_feature = Features.by_application(NimbusConstants.Application.DESKTOP)[0]
        remote_schema = desktop_feature.get_jsonschema()

        self.mock_requests_get.assert_called_once_with(
            "https://hg.mozilla.org/mozilla-central/raw-file/tip/path/to/schema.json"
        )

        self.assertEqual(json.loads(remote_schema), {"schema": True})

    def test_raises_request_error(self):
        self.setup_request_error()

        with self.assertRaises(requests.ConnectionError):
            desktop_feature = Features.by_application(
                NimbusConstants.Application.DESKTOP
            )[0]
            desktop_feature.get_jsonschema()

    def test_returns_none_for_invalid_json(self):
        self.setup_json_error()

        desktop_feature = Features.by_application(NimbusConstants.Application.DESKTOP)[0]
        self.assertIsNone(desktop_feature.get_jsonschema())


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
