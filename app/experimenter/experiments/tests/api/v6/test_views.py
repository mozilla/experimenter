import json

from django.test import TestCase
from django.urls import reverse

from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory


class TestNimbusExperimentViewSet(TestCase):
    def test_list_view_serializes_experiments(self):
        experiments = []

        for status in NimbusExperiment.Status:
            if status not in [
                NimbusExperiment.Status.DRAFT,
                NimbusExperiment.Status.REVIEW,
            ]:
                experiments.append(
                    NimbusExperimentFactory.create_with_status(status.value, slug=status)
                )

        response = self.client.get(
            reverse("nimbus-experiment-rest-list"),
        )
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)
        json_slugs = set([d["id"] for d in json_data])
        expected_slugs = set(e.slug for e in experiments)
        self.assertEqual(json_slugs, expected_slugs)

    def test_get_nimbus_experiment_returns_expected_data(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE
        )

        response = self.client.get(
            reverse(
                "nimbus-experiment-rest-detail",
                kwargs={"slug": experiment.slug},
            ),
        )

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        serialized_experiment = NimbusExperimentSerializer(experiment).data

        self.maxDiff = None
        self.assertEqual(serialized_experiment, json_data)
