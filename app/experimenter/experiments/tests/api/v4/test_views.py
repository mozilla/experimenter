import json

from django.test import TestCase
from django.urls import reverse

from experimenter.experiments.models import Experiment
from experimenter.experiments.constants import ExperimentConstants
from experimenter.experiments.api.v4.serializers import ExperimentRapidRecipeSerializer
from experimenter.experiments.tests.factories import ExperimentFactory


class TestExperimentListView(TestCase):
    def test_list_view_serializes_experiments(self):
        experiments = []

        for i in range(3):
            experiment = ExperimentFactory.create_with_variants(
                status=Experiment.STATUS_DRAFT,
                type=ExperimentConstants.TYPE_RAPID,
                objectives="gotta go fast",
                audience="us_only",
                features=["pinned_tabs"],
            )
            experiments.append(experiment)

        response = self.client.get(reverse("experiment-rapid-recipe-list"),)
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)

        serialized_experiments = ExperimentRapidRecipeSerializer(
            Experiment.objects.get_prefetched(), many=True
        ).data

        self.maxDiff = None
        self.assertEqual(serialized_experiments, json_data)


class TestExperimentRapidRecipeView(TestCase):
    def test_get_rapid_experiment_recipe_returns_recipe_info_for_experiment(self):
        experiment = ExperimentFactory.create_with_variants(
            status=Experiment.STATUS_DRAFT,
            type=ExperimentConstants.TYPE_RAPID,
            objectives="gotta go fast",
            audience="us_only",
            features=["pinned_tabs"],
        )

        response = self.client.get(
            reverse("experiment-rapid-recipe-detail", kwargs={"slug": experiment.slug}),
        )

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        serialized_experiment = ExperimentRapidRecipeSerializer(experiment).data

        self.maxDiff = None
        self.assertEqual(serialized_experiment, json_data)
