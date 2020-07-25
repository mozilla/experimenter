import datetime
import json
import os
from jsonschema import validate

from django.test import TestCase

from mozilla_nimbus_shared import get_data

from experimenter.experiments.models import Experiment, ExperimentBucketNamespace
from experimenter.experiments.tests.factories import (
    ExperimentFactory,
    ExperimentVariantFactory,
)
from experimenter.experiments.api.v4.serializers import ExperimentRapidRecipeSerializer

NIMBUS_DATA = get_data()


class TestExperimentRapidRecipeSerializer(TestCase):
    def test_serializer_outputs_expected_schema_for_draft(self):
        audience = "us_only"
        features = ["pinned_tabs", "picture_in_picture"]
        normandy_slug = "experimenter-normandy-slug"
        experiment = ExperimentFactory.create(
            status=Experiment.STATUS_DRAFT,
            type=Experiment.TYPE_RAPID,
            rapid_type=Experiment.RAPID_AA_CFR,
            audience=audience,
            features=features,
            normandy_slug=normandy_slug,
            firefox_min_version="80.0",
            proposed_duration=28,
            proposed_enrollment=7,
            proposed_start_date=None,
        )

        ExperimentVariantFactory.create(
            experiment=experiment, slug="control", is_control=True
        )
        ExperimentVariantFactory.create(experiment=experiment, slug="variant-2")

        serializer = ExperimentRapidRecipeSerializer(experiment)
        data = serializer.data.copy()

        arguments = data.pop("arguments")
        branches = arguments.pop("branches")

        self.assertDictEqual(
            data,
            {
                "id": normandy_slug,
                "filter_expression": "env.version|versionCompare('80.0') >= 0",
                "targeting": "localeLanguageCode == 'en' && region == 'US'"
                " && browserSettings.update.channel == 'release'",
                "enabled": True,
            },
        )

        self.maxDiff = None
        self.assertDictEqual(
            dict(arguments),
            {
                "userFacingName": experiment.name,
                "userFacingDescription": experiment.public_description,
                "slug": normandy_slug,
                "active": True,
                "isEnrollmentPaused": False,
                "proposedEnrollment": experiment.proposed_enrollment,
                "features": features,
                "referenceBranch": "control",
                "startDate": None,
                "endDate": None,
                "bucketConfig": None,
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

    def test_serializer_outputs_expected_schema_for_review(self):
        audience = "us_only"
        features = ["pinned_tabs", "picture_in_picture"]
        normandy_slug = "experimenter-normandy-slug"
        today = datetime.date.today()
        experiment = ExperimentFactory.create(
            status=Experiment.STATUS_REVIEW,
            type=Experiment.TYPE_RAPID,
            rapid_type=Experiment.RAPID_AA_CFR,
            audience=audience,
            features=features,
            normandy_slug=normandy_slug,
            firefox_min_version="80.0",
            proposed_duration=28,
            proposed_enrollment=7,
            proposed_start_date=today,
        )

        ExperimentVariantFactory.create(
            experiment=experiment, slug="control", is_control=True
        )
        ExperimentVariantFactory.create(
            experiment=experiment, slug="variant-2", is_control=False
        )

        ExperimentBucketNamespace.request_namespace_buckets(
            experiment.normandy_slug, experiment, 100
        )

        serializer = ExperimentRapidRecipeSerializer(experiment)
        data = serializer.data.copy()

        fn = os.path.join(os.path.dirname(__file__), "experimentRecipe.json")
        with open(fn, "r") as f:
            json_schema = json.load(f)
        self.assertIsNone(validate(instance=data, schema=json_schema))

        arguments = data.pop("arguments")
        branches = arguments.pop("branches")

        self.assertDictEqual(
            data,
            {
                "id": normandy_slug,
                "filter_expression": "env.version|versionCompare('80.0') >= 0",
                "targeting": "localeLanguageCode == 'en' && region == 'US'"
                " && browserSettings.update.channel == 'release'",
                "enabled": True,
            },
        )

        bucket = experiment.bucket

        self.maxDiff = None
        self.assertDictEqual(
            dict(arguments),
            {
                "userFacingName": experiment.name,
                "userFacingDescription": experiment.public_description,
                "slug": normandy_slug,
                "active": True,
                "isEnrollmentPaused": False,
                "proposedEnrollment": experiment.proposed_enrollment,
                "features": features,
                "referenceBranch": "control",
                "startDate": today.isoformat(),
                "endDate": (today + datetime.timedelta(days=28)).isoformat(),
                "bucketConfig": {
                    "count": bucket.count,
                    "namespace": bucket.namespace.name,
                    "randomizationUnit": bucket.namespace.randomization_unit,
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
