import os
import json
from datetime import datetime
from jsonschema import validate
from django.test import TestCase

from experimenter.experiments.models import Experiment
from experimenter.experiments.tests.factories import (
    ExperimentFactory,
    ExperimentVariantFactory,
)
from experimenter.kinto.serializers import ExperimentRapidRecipeSerializer


class TestExperimentRapidSerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        audience = Experiment.RAPID_AUDIENCE_CHOICES[0][1]
        features = [feature[0] for feature in Experiment.RAPID_FEATURE_CHOICES]
        normandy_slug = "experimenter-normandy-slug"
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_RAPID,
            rapid_type=Experiment.RAPID_AA_CFR,
            audience=audience,
            features=features,
            normandy_slug=normandy_slug,
            proposed_enrollment=9,
        )

        ExperimentVariantFactory.create(
            experiment=experiment, slug="control", is_control=True
        )
        ExperimentVariantFactory.create(experiment=experiment, slug="variant-2")

        serializer = ExperimentRapidRecipeSerializer(experiment)
        data = serializer.data

        fn = os.path.join(os.path.dirname(__file__), "experimentRecipe.json")

        with open(fn) as f:
            json_schema = json.loads(f.read())
        self.assertIsNone(validate(instance=data, schema=json_schema))

        arguments = data.pop("arguments")
        branches = arguments.pop("branches")
        start_date = arguments.pop("startDate")

        self.maxDiff = None
        self.assertDictEqual(
            data,
            {"id": normandy_slug, "filter_expression": "AUDIENCE1", "enabled": True},
        )
        self.assertEqual(
            datetime.fromisoformat(start_date).day, datetime.today().day,
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
                {"ratio": 33, "slug": "variant-2", "value": {}},
                {"ratio": 33, "slug": "control", "value": {}},
            ],
        )
