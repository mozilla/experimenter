import datetime
import json
import os
from jsonschema import validate

from django.test import TestCase
from django.conf import settings

from experimenter.experiments.models import Experiment
from experimenter.experiments.tests.factories import (
    ExperimentFactory,
    ExperimentVariantFactory,
)
from experimenter.experiments.api.v4.serializers import ExperimentRapidRecipeSerializer
from experimenter.openidc.tests.factories import UserFactory


class TestExperimentRapidRecipeSerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        audience = Experiment.RAPID_AUDIENCE_CHOICES[0][1]
        features = [feature[0] for feature in Experiment.RAPID_FEATURE_CHOICES]
        normandy_slug = "experimenter-normandy-slug"
        today = datetime.datetime.today()
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_RAPID,
            rapid_type=Experiment.RAPID_AA_CFR,
            audience=audience,
            features=features,
            normandy_slug=normandy_slug,
            proposed_enrollment=9,
            proposed_start_date=today,
        )

        ExperimentVariantFactory.create(
            experiment=experiment, slug="control", is_control=True
        )
        ExperimentVariantFactory.create(experiment=experiment, slug="variant-2")

        serializer = ExperimentRapidRecipeSerializer(experiment)
        data = serializer.data

        fn = os.path.join(os.path.dirname(__file__), "experimentRecipe.json")

        with open(fn, "r") as f:
            json_schema = json.load(f)
        self.assertIsNone(validate(instance=data, schema=json_schema))

        arguments = data.pop("arguments")
        branches = arguments.pop("branches")

        self.assertDictEqual(
            data,
            {"id": normandy_slug, "filter_expression": "AUDIENCE 1", "enabled": True},
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
