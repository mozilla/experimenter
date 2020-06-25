from time import time
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
        features = ["FEATURE 1", "FEATURE 2"]
        normandy_slug = "experimenter-normandy-slug"
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_RAPID,
            rapid_type=Experiment.RAPID_AA_CFR,
            audience=audience,
            features=features,
            normandy_slug=normandy_slug,
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
            {"id": normandy_slug, "filter_expression": "AUDIENCE1", "enabled": "true"},
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
                "startDate": int(time()),
                "proposedEnrollment": experiment.proposed_enrollment,
                "features": experiment.features,
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
