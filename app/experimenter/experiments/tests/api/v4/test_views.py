import json

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from parameterized import parameterized

from experimenter.experiments.models import Experiment
from experimenter.experiments.constants import ExperimentConstants
from experimenter.experiments.api.v4.serializers import ExperimentRapidRecipeSerializer
from experimenter.experiments.tests.factories import ExperimentFactory


class TestExperimentListView(TestCase):
    def test_list_view_serializes_experiments(self):
        experiments = []
        user_email = "user@example.com"

        for i in range(3):
            experiment = ExperimentFactory.create_with_variants(
                type=ExperimentConstants.TYPE_RAPID,
                objectives="gotta go fast",
                audience="AUDIENCE 1",
                features=["FEATURE 1"],
            )
            experiments.append(experiment)

        response = self.client.get(
            reverse("experiment-rapid-recipe-list"),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)

        serialized_experiments = ExperimentRapidRecipeSerializer(
            Experiment.objects.get_prefetched(), many=True
        ).data

        self.assertEqual(serialized_experiments, json_data)


class TestExperimentRapidRecipeView(TestCase):
    def test_get_rapid_experiment_recipe_returns_recipe_info_for_experiment(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_RAPID)

        response = self.client.get(
            reverse("experiment-rapid-recipe-detail", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        serialized_experiment = ExperimentRapidRecipeSerializer(experiment).data
        self.assertEqual(serialized_experiment, json_data)
