from django.test import TestCase

from experimenter.experiments.api.v5.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory


class TestNimbusExperimentSerializer(TestCase):
    maxDiff = None

    def test_serializer_outputs_expected_schema(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.ACCEPTED,
        )

        serializer = NimbusExperimentSerializer(experiment)
        data = serializer.data

        self.assertDictEqual(
            data,
            {
                "application": experiment.application,
                "hypothesis": experiment.hypothesis,
                "name": experiment.name,
                "public_description": experiment.public_description,
                "slug": experiment.slug,
            },
        )
