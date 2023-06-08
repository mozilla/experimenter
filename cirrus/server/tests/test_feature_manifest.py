import json
import unittest

from cirrus.feature_manifest import FeatureManifestLanguage
from cirrus.sdk import SDK


class FeatureManifestLanguageTestCase(unittest.TestCase):
    maxDiff = None

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

    def test_compute_feature_configurations_with_partial_config(self):
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
                    "featureId": "imported-module-1-included-feature-1",
                    "value": {"enabled": False},
                },
            },
            {
                "slug": "treatment",
                "ratio": 1,
                "feature": {
                    "featureId": "imported-module-1-included-feature-1",
                    "value": {"enabled": True},
                },
            },
        ]

        experiment_slug = "experiment-slug"
        enrollment_id = "c3d0aa7b-c52c-4548-8a9a-13475e445cf2"

        experiment = {
            "schemaVersion": "1.0.0",
            "slug": experiment_slug,
            "userFacingName": "",
            "userFacingDescription": "",
            "appId": "test_app_id",
            "appName": "test_app_name",
            "channel": "developer",
            "targeting": '(is_already_enrolled) || (username in ["test", "jeddai"])',
            "bucketConfig": bucket_config,
            "isRollout": False,
            "isEnrollmentPaused": False,
            "proposedEnrollment": 10,
            "branches": branches,
            "featureIds": ["imported-module-1-included-feature-1"],
        }

        data = json.dumps({"data": [experiment]})
        targeting_context = {"clientId": "test", "requestContext": {"username": "test"}}
        sdk = SDK()
        sdk.set_experiments(data)
        result = sdk.compute_enrollments(targeting_context)

        expected_result = {
            "enrolledFeatureConfigMap": {
                "imported-module-1-included-feature-1": {
                    "branch": "treatment",
                    "feature": {
                        "featureId": "imported-module-1-included-feature-1",
                        "value": {"enabled": True},
                    },
                    "featureId": "imported-module-1-included-feature-1",
                    "slug": experiment_slug,
                }
            },
            "enrollments": [
                {
                    "slug": experiment_slug,
                    "status": {
                        "Enrolled": {
                            "branch": "treatment",
                            "enrollment_id": enrollment_id,
                            "reason": "Qualified",
                        }
                    },
                }
            ],
            "events": [
                {
                    "branch_slug": "treatment",
                    "change": "Enrollment",
                    "enrollment_id": enrollment_id,
                    "experiment_slug": experiment_slug,
                    "reason": None,
                }
            ],
        }

        # self.assertEqual(result, expected_result)
        self.assertEqual(
            result["enrolledFeatureConfigMap"]["imported-module-1-included-feature-1"][
                "branch"
            ],
            expected_result["enrolledFeatureConfigMap"][
                "imported-module-1-included-feature-1"
            ]["branch"],
        )

        self.assertEqual(
            result["enrolledFeatureConfigMap"]["imported-module-1-included-feature-1"][
                "feature"
            ]["value"],
            expected_result["enrolledFeatureConfigMap"][
                "imported-module-1-included-feature-1"
            ]["feature"]["value"],
        )
        self.assertEqual(
            result["enrollments"][0]["status"]["Enrolled"]["branch"],
            expected_result["enrollments"][0]["status"]["Enrolled"]["branch"],
        )
        self.assertEqual(
            result["enrollments"][0]["status"]["Enrolled"]["reason"],
            expected_result["enrollments"][0]["status"]["Enrolled"]["reason"],
        )
        self.assertEqual(
            result["events"][0]["branch_slug"],
            expected_result["events"][0]["branch_slug"],
        )
        self.assertEqual(
            result["events"][0]["change"],
            expected_result["events"][0]["change"],
        )
        self.assertEqual(
            result["events"][0]["reason"],
            expected_result["events"][0]["reason"],
        )
        fml = FeatureManifestLanguage()

        result = fml.compute_feature_configurations(result)

        self.assertEqual(
            result, {"example-feature": {"enabled": False, "something": "wicked"}}
        )
