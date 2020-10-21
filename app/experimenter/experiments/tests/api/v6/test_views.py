import json

from django.test import TestCase
from django.urls import reverse

from experimenter.experiments.api.v6.serializers import (
    NimbusExperimentSerializer,
    NimbusProbeSetSerializer,
)
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusProbeSetFactory,
)


class TestNimbusExperimentViewSet(TestCase):
    maxDiff = None

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
        self.assertEqual(NimbusExperimentSerializer(experiment).data, json_data)


class TestNimbusProbeSetViewSet(TestCase):
    def test_list_view_serializes_probesets(self):
        probesets = [NimbusProbeSetFactory() for i in range(3)]

        response = self.client.get(
            reverse("nimbus-probeset-rest-list"),
        )
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)
        json_slugs = set([d["slug"] for d in json_data])
        expected_slugs = set(p.slug for p in probesets)
        self.assertEqual(json_slugs, expected_slugs)

    def test_get_nimbus_experiment_returns_expected_data(self):
        probeset = NimbusProbeSetFactory()

        response = self.client.get(
            reverse(
                "nimbus-probeset-rest-detail",
                kwargs={"slug": probeset.slug},
            ),
        )

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        self.assertEqual(NimbusProbeSetSerializer(probeset).data, json_data)
