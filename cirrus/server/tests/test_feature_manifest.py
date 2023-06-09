import json
import unittest
from parameterized import parameterized

from cirrus.feature_manifest import FeatureManifestLanguage
from cirrus.sdk import SDK
from fml_sdk import FmlError


class FeatureManifestLanguageTestCase(unittest.TestCase):
    def setUp(self):
        self.fml = FeatureManifestLanguage()
        self.sdk = SDK()

    def test_compute_feature_configurations_always_return_default_config(self):
        enrolled_partial_configuration = {
            "enrolledFeatureConfigMap": {},
            "enrollments": [],
            "events": [],
        }

        result = self.fml.compute_feature_configurations(enrolled_partial_configuration)

        self.assertEqual(
            result, {"example-feature": {"enabled": False, "something": "wicked"}}
        )

    @parameterized.expand(
        [
            [
                "imported-module-1-included-feature-1",
                False,
            ],
            ["example-feature", True],
            ["", False],
        ]
    )
    def test_compute_feature_configurations_feature(
        self, feature_name, expected_feature_status
    ):
        enrolled_partial_configuration = {
            "enrolledFeatureConfigMap": {
                feature_name: {
                    "branch": "treatment",
                    "feature": {
                        "featureId": feature_name,
                        "value": {"enabled": True},
                    },
                    "featureId": feature_name,
                    "slug": "experiment_slug",
                }
            },
            "enrollments": [
                {
                    "slug": "experiment_slug",
                    "status": {
                        "Enrolled": {
                            "branch": "treatment",
                            "enrollment_id": "enrollment_id",
                            "reason": "Qualified",
                        }
                    },
                }
            ],
            "events": [
                {
                    "branch_slug": "treatment",
                    "change": "Enrollment",
                    "enrollment_id": "enrollment_id",
                    "experiment_slug": "experiment_slug",
                    "reason": None,
                }
            ],
        }

        result = self.fml.compute_feature_configurations(enrolled_partial_configuration)

        self.assertEqual(
            result,
            {
                "example-feature": {
                    "enabled": expected_feature_status,
                    "something": "wicked",
                }
            },
        )

    def test_compute_feature_configurations_invalid_key_merge_errors(self):
        enrolled_partial_configuration = {
            "enrolledFeatureConfigMap": {
                "example-feature": {
                    "branch": "treatment",
                    "feature": {
                        "featureId": "example-feature",
                        "value": {"enabled1": True},  # invalid
                    },
                    "featureId": "example-feature",
                    "slug": "experiment-slug",
                }
            },
            "enrollments": [],
            "events": [],
        }

        result = self.fml.compute_feature_configurations(enrolled_partial_configuration)

        self.assertEqual(
            result, {"example-feature": {"enabled": False, "something": "wicked"}}
        )  # returns default config
        self.assertEqual(len(self.fml.merge_errors), 1)
        assert isinstance(self.fml.merge_errors[0], FmlError)

    def test_compute_feature_configurations_targeting_doesnt_match(self):
        bucket_config = {
            "randomizationUnit": "user_id",
            "count": 100,
            "namespace": "",
            "start": 1,
            "total": 100,
        }

        branches = [
            {
                "slug": "control",
                "ratio": 1,
                "feature": {
                    "featureId": "example-feature",
                    "value": {"enabled": False},
                },
            },
            {
                "slug": "treatment",
                "ratio": 1,
                "feature": {
                    "featureId": "example-feature",
                    "value": {"enabled": True},
                },
            },
        ]

        experiment = {
            "schemaVersion": "1.0.0",
            "slug": "experiment-slug",
            "userFacingName": "",
            "userFacingDescription": "",
            "appId": "test_app_id",
            "appName": "test_app_name",
            "channel": "developer",
            "targeting": '(is_already_enrolled) || (username in ["test", "test2"])',
            "bucketConfig": bucket_config,
            "isRollout": False,
            "isEnrollmentPaused": False,
            "proposedEnrollment": 10,
            "branches": branches,
            "featureIds": ["example-feature"],
        }

        data = json.dumps({"data": [experiment]})
        targeting_context = {
            "clientId": "test",
            "requestContext": {"username": "test1"},
        }
        self.sdk.set_experiments(data)
        enrolled_partial_configuration = self.sdk.compute_enrollments(targeting_context)
        self.assertEqual(
            enrolled_partial_configuration,
            {
                "enrolledFeatureConfigMap": {},
                "enrollments": [
                    {
                        "slug": "experiment-slug",
                        "status": {"NotEnrolled": {"reason": "NotTargeted"}},
                    }
                ],
                "events": [],
            },
        )

        result = self.fml.compute_feature_configurations(enrolled_partial_configuration)

        self.assertEqual(
            result, {"example-feature": {"enabled": False, "something": "wicked"}}
        )  # default config
        self.assertEqual(len(self.fml.merge_errors), 0)
