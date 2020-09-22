from django.test import TestCase

from experimenter.experiments.api.v4.serializers import ExperimentRapidRecipeSerializer
from experimenter.experiments.models import Experiment
from experimenter.experiments.tests.factories import ExperimentRapidFactory


class TestExperimentRapidRecipeSerializer(TestCase):
    maxDiff = None

    def test_serializer_outputs_expected_schema_for_accepted(self):
        audience = "us_only"
        features = ["pinned_tabs", "picture_in_picture"]
        experiment = ExperimentRapidFactory.create_with_status(
            Experiment.STATUS_ACCEPTED,
            audience=audience,
            features=features,
            firefox_channel=Experiment.CHANNEL_RELEASE,
            firefox_min_version="80.0",
        )

        serializer = ExperimentRapidRecipeSerializer(experiment)
        data = serializer.data

        arguments = data.pop("arguments")
        branches = arguments.pop("branches")

        self.assertDictEqual(
            data,
            {
                "id": experiment.recipe_slug,
                "filter_expression": "env.version|versionCompare('80.!') >= 0",
                "targeting": f'[userId, "{experiment.recipe_slug}"]'
                "|bucketSample(0, 100, 10000) "
                "&& localeLanguageCode == 'en' && region == 'US' "
                "&& browserSettings.update.channel == 'release'",
                "enabled": True,
            },
        )

        self.assertDictEqual(
            dict(arguments),
            {
                "userFacingName": experiment.name,
                "userFacingDescription": experiment.public_description,
                "slug": experiment.recipe_slug,
                "active": True,
                "isEnrollmentPaused": False,
                "endDate": None,
                "proposedEnrollment": experiment.proposed_enrollment,
                "features": features,
                "referenceBranch": "control",
                "startDate": None,
                "bucketConfig": {
                    "count": experiment.bucket.count,
                    "namespace": experiment.bucket.namespace.name,
                    "randomizationUnit": "userId",
                    "start": experiment.bucket.start,
                    "total": experiment.bucket.namespace.total,
                },
            },
        )
        converted_branches = [dict(branch) for branch in branches]
        self.assertEqual(
            converted_branches,
            [
                {"ratio": 33, "slug": "treatment", "value": None},
                {"ratio": 33, "slug": "control", "value": None},
            ],
        )

    def test_serializer_outputs_expected_schema_for_live(self):
        audience = "us_only"
        features = ["pinned_tabs", "picture_in_picture"]
        experiment = ExperimentRapidFactory.create_with_status(
            Experiment.STATUS_LIVE,
            audience=audience,
            features=features,
            firefox_channel=Experiment.CHANNEL_RELEASE,
            firefox_min_version="80.0",
        )

        serializer = ExperimentRapidRecipeSerializer(experiment)
        data = serializer.data

        arguments = data.pop("arguments")
        branches = arguments.pop("branches")

        self.assertDictEqual(
            data,
            {
                "id": experiment.recipe_slug,
                "filter_expression": "env.version|versionCompare('80.!') >= 0",
                "targeting": f'[userId, "{experiment.recipe_slug}"]'
                "|bucketSample(0, 100, 10000) "
                "&& localeLanguageCode == 'en' && region == 'US' "
                "&& browserSettings.update.channel == 'release'",
                "enabled": True,
            },
        )

        self.assertDictEqual(
            dict(arguments),
            {
                "userFacingName": experiment.name,
                "userFacingDescription": experiment.public_description,
                "slug": experiment.recipe_slug,
                "active": True,
                "isEnrollmentPaused": False,
                "endDate": experiment.end_date.isoformat(),
                "proposedEnrollment": experiment.proposed_enrollment,
                "features": features,
                "referenceBranch": "control",
                "startDate": experiment.start_date.isoformat(),
                "bucketConfig": {
                    "count": experiment.bucket.count,
                    "namespace": experiment.bucket.namespace.name,
                    "randomizationUnit": "userId",
                    "start": experiment.bucket.start,
                    "total": experiment.bucket.namespace.total,
                },
            },
        )
        converted_branches = [dict(branch) for branch in branches]
        self.assertEqual(
            converted_branches,
            [
                {"ratio": 33, "slug": "treatment", "value": None},
                {"ratio": 33, "slug": "control", "value": None},
            ],
        )
