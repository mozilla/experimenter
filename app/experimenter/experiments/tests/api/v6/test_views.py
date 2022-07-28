import json

from django.test import TestCase
from django.urls import reverse

from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory


class TestNimbusExperimentViewSet(TestCase):
    maxDiff = None

    def test_list_view_serializes_experiments(self):
        experiments = []

        for lifecycle in NimbusExperimentFactory.Lifecycles:
            final_status = lifecycle.value[-1].value
            if final_status["status"] not in [
                NimbusExperiment.Status.DRAFT,
            ]:
                experiments.append(
                    NimbusExperimentFactory.create_with_lifecycle(
                        lifecycle, slug=lifecycle.name
                    )
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
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            slug="test-rest-detail",
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

    def test_filters_on_is_first_run(self):
        first_run_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            is_first_run=True,
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            is_first_run=False,
        )

        response = self.client.get(
            reverse("nimbus-experiment-rest-list"),
            {"is_first_run": "True"},
        )

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        self.assertEqual(len(json_data), 1)
        self.assertEqual(json_data[0]["slug"], first_run_experiment.slug)
