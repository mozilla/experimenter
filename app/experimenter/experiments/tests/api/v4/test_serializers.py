import datetime

from django.test import TestCase

from experimenter.experiments.models import Experiment, ExperimentBucketNamespace
from experimenter.experiments.tests.factories import (
    ExperimentFactory,
    ExperimentVariantFactory,
)
from experimenter.experiments.api.v4.serializers import ExperimentRapidRecipeSerializer


class TestExperimentRapidRecipeSerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        audience = "us_only"
        features = ["pinned_tabs", "picture_in_picture"]
        normandy_slug = "experimenter-normandy-slug"
        today = datetime.datetime.today()
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_RAPID,
            rapid_type=Experiment.RAPID_AA_CFR,
            audience=audience,
            features=features,
            normandy_slug=normandy_slug,
            firefox_min_version="80.0",
            proposed_enrollment=9,
            proposed_start_date=today,
        )

        ExperimentVariantFactory.create(
            experiment=experiment, slug="control", is_control=True
        )
        ExperimentVariantFactory.create(experiment=experiment, slug="variant-2")

        serializer = ExperimentRapidRecipeSerializer(experiment)
        data = serializer.data

        arguments = data.pop("arguments")
        branches = arguments.pop("branches")

        self.assertDictEqual(
            data,
            {
                "id": normandy_slug,
                "filter_expression": "env.version|versionCompare('80.0') >= 0",
                "targeting": None,
                "enabled": True,
            },
        )

        self.assertDictEqual(
            dict(arguments),
            {
                "userFacingName": experiment.name,
                "userFacingDescription": experiment.public_description,
                "slug": normandy_slug,
                "active": True,
                "isEnrollmentPaused": False,
                "endDate": None,
                "proposedEnrollment": experiment.proposed_enrollment,
                "features": features,
                "referenceBranch": "control",
                "startDate": today.isoformat(),
                "bucketConfig": {
                    "count": 0,
                    "namespace": "",
                    "randomizationUnit": "normandy_id",
                    "start": 0,
                    "total": 10000,
                },
            },
        )
        converted_branches = [dict(branch) for branch in branches]
        self.assertEqual(
            converted_branches,
            [
                {"ratio": 33, "slug": "variant-2", "value": None},
                {"ratio": 33, "slug": "control", "value": None},
            ],
        )

    def test_serializer_outputs_expected_schema_with_nameSpace_bucket(self):
        audience = "us_only"
        features = ["pinned_tabs", "picture_in_picture"]
        normandy_slug = "experimenter-normandy-slug"
        today = datetime.datetime.today()
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_RAPID,
            rapid_type=Experiment.RAPID_AA_CFR,
            audience=audience,
            features=features,
            normandy_slug=normandy_slug,
            firefox_min_version="80.0",
            firefox_channel=Experiment.CHANNEL_RELEASE,
            proposed_enrollment=9,
            proposed_start_date=today,
        )

        ExperimentVariantFactory.create(
            experiment=experiment, slug="control", is_control=True
        )
        ExperimentVariantFactory.create(experiment=experiment, slug="variant-2")

        ExperimentBucketNamespace.request_namespace_buckets(
            experiment.normandy_slug, experiment, 100
        )

        serializer = ExperimentRapidRecipeSerializer(experiment)
        data = serializer.data

        arguments = data.pop("arguments")
        branches = arguments.pop("branches")

        self.assertDictEqual(
            data,
            {
                "id": normandy_slug,
                "filter_expression": "env.version|versionCompare('80.0') >= 0",
                "targeting": '[userId, "experimenter-normandy-slug"]'
                "|bucketSample(0, 100, 10000) "
                "&& localeLanguageCode == 'en' && region == 'US' "
                "&& browserSettings.update.channel == 'release'",
                "enabled": True,
            },
        )

        bucket = experiment.bucket

        self.assertDictEqual(
            dict(arguments),
            {
                "userFacingName": experiment.name,
                "userFacingDescription": experiment.public_description,
                "slug": normandy_slug,
                "active": True,
                "isEnrollmentPaused": False,
                "endDate": None,
                "proposedEnrollment": experiment.proposed_enrollment,
                "features": features,
                "referenceBranch": "control",
                "startDate": today.isoformat(),
                "bucketConfig": {
                    "count": bucket.count,
                    "namespace": bucket.namespace.name,
                    "randomizationUnit": "userId",
                    "start": bucket.start,
                    "total": bucket.namespace.total,
                },
            },
        )
        converted_branches = [dict(branch) for branch in branches]
        self.assertEqual(
            converted_branches,
            [
                {"ratio": 33, "slug": "variant-2", "value": None},
                {"ratio": 33, "slug": "control", "value": None},
            ],
        )
