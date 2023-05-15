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
            experiment = NimbusExperimentFactory.create_with_lifecycle(
                lifecycle, slug=lifecycle.name
            )

            if experiment.status not in [
                NimbusExperiment.Status.DRAFT,
            ]:
                experiments.append(experiment)

        experiments = sorted(experiments, key=lambda e: e.slug)

        response = self.client.get(
            reverse("nimbus-experiment-rest-list"),
        )
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)
        json_slugs = [d["id"] for d in json_data]
        expected_slugs = [e.slug for e in experiments]
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


class TestNimbusExperimentDraftViewSet(TestCase):
    maxDiff = None

    def test_detail_view_serializes_draft_experiments(self):
        draft_slugs = []
        non_draft_slugs = []

        for lifecycle in NimbusExperimentFactory.Lifecycles:
            experiment = NimbusExperimentFactory.create_with_lifecycle(
                lifecycle,
                slug=lifecycle.name,
            )

            if experiment.status == NimbusExperiment.Status.DRAFT:
                draft_slugs.append(experiment.slug)
            else:
                non_draft_slugs.append(experiment.slug)

        for slug in draft_slugs:
            response = self.client.get(
                reverse("nimbus-experiment-draft-rest-detail", kwargs={"slug": slug})
            )
            self.assertEqual(response.status_code, 200)

        for slug in non_draft_slugs:
            response = self.client.get(
                reverse("nimbus-experiment-draft-rest-detail", kwargs={"slug": slug})
            )
            self.assertEqual(response.status_code, 404)

    def test_list_view_serializes_draft_experiments(self):
        expected_slugs = []

        for lifecycle in NimbusExperimentFactory.Lifecycles:
            experiment = NimbusExperimentFactory.create_with_lifecycle(
                lifecycle,
                slug=lifecycle.name,
            )

            if experiment.status == NimbusExperiment.Status.DRAFT:
                expected_slugs.append(experiment.slug)

        response = self.client.get(reverse("nimbus-experiment-draft-rest-list"))
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)
        slugs = [recipe["slug"] for recipe in json_data]
        self.assertEqual(set(slugs), set(expected_slugs))

    def test_list_view_filter_localized(self):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED, slug="experiment"
        )

        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            slug="localized_experiment",
            is_localized=True,
            localizations=json.dumps(
                {
                    "en-US": {},
                    "en-CA": {},
                }
            ),
        )

        response = self.client.get(
            f"{reverse('nimbus-experiment-draft-rest-list')}?is_localized=1"
        )
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)
        slugs = [recipe["slug"] for recipe in json_data]
        self.assertEqual(slugs, ["localized_experiment"])


class TestNimbusExperimentFirstRunViewSet(TestCase):
    maxDiff = None

    def test_list_view_serializes_live_first_run_experiments(self):
        experiments = []

        for lifecycle in NimbusExperimentFactory.Lifecycles:
            experiment = NimbusExperimentFactory.create_with_lifecycle(
                lifecycle, slug=lifecycle.name, is_first_run=True
            )

            if experiment.status == NimbusExperiment.Status.LIVE:
                experiments.append(experiment)

        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING, is_first_run=False
        )

        experiments = sorted(experiments, key=lambda e: e.slug)

        response = self.client.get(
            reverse("nimbus-experiment-rest-first-run-list"),
        )
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)
        json_slugs = [d["id"] for d in json_data]
        expected_slugs = [e.slug for e in experiments]
        self.assertEqual(json_slugs, expected_slugs)
