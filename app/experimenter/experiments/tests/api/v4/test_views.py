import json

from django.test import TestCase
from django.urls import reverse

from experimenter.experiments.api.v4.serializers import ExperimentRapidRecipeSerializer
from experimenter.experiments.models import Experiment
from experimenter.experiments.tests.factories import ExperimentRapidFactory


class TestExperimentListView(TestCase):
    def test_list_view_serializes_experiments(self):
        experiments = []

        for status, _ in Experiment.STATUS_CHOICES:
            experiment = ExperimentRapidFactory.create_with_status(status)

            if status not in [Experiment.STATUS_DRAFT, Experiment.STATUS_REVIEW]:
                experiments.append(experiment)

        response = self.client.get(
            reverse("experiment-rapid-recipe-list"),
        )
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)
        json_slugs = set([d["id"] for d in json_data])
        expected_slugs = set(e.recipe_slug for e in experiments)
        self.assertEqual(json_slugs, expected_slugs)

        json_data_names = set([d["arguments"]["userFacingName"] for d in json_data])
        expected_names = set(e.name for e in experiments)
        self.assertEqual(json_data_names, expected_names)


class TestExperimentRapidRecipeView(TestCase):
    def test_get_rapid_experiment_recipe_returns_recipe_info_for_experiment(self):
        experiment = ExperimentRapidFactory.create_with_status(Experiment.STATUS_LIVE)

        response = self.client.get(
            reverse(
                "experiment-rapid-recipe-detail",
                kwargs={"recipe_slug": experiment.recipe_slug},
            ),
        )

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        serialized_experiment = ExperimentRapidRecipeSerializer(experiment).data

        self.maxDiff = None
        self.assertEqual(serialized_experiment, json_data)

    def test_get_rapid_experiment_recipe_returns_404_for_draft(self):
        experiment = ExperimentRapidFactory.create_with_status(Experiment.STATUS_DRAFT)

        response = self.client.get(
            reverse(
                "experiment-rapid-recipe-detail",
                kwargs={"recipe_slug": experiment.recipe_slug},
            ),
        )

        self.assertEqual(response.status_code, 404)
