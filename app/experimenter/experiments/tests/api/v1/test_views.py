import json

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from parameterized import parameterized

from experimenter.experiments.api.v1.serializers import ExperimentSerializer
from experimenter.experiments.constants import ExperimentConstants
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.legacy.legacy_experiments.models import Experiment
from experimenter.normandy.serializers import ExperimentRecipeSerializer


class TestExperimentListView(TestCase):
    def test_list_view_serializes_experiments(self):
        experiments = []

        for i in range(3):
            experiment = ExperimentFactory.create_with_variants()
            experiments.append(experiment)

        response = self.client.get(reverse("experiments-api-list"))
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)

        serialized_experiments = ExperimentSerializer(
            Experiment.objects.get_prefetched(), many=True
        ).data

        self.assertEqual(serialized_experiments, json_data)

    def test_list_view_filters_by_status(self):
        pending_experiments = []

        # new experiments should be excluded
        for i in range(2):
            ExperimentFactory.create_with_variants()

        # pending experiments should be included
        for i in range(3):
            experiment = ExperimentFactory.create_with_variants()
            experiment.status = experiment.STATUS_REVIEW
            experiment.save()
            pending_experiments.append(experiment)

        response = self.client.get(
            reverse("experiments-api-list"), {"status": Experiment.STATUS_REVIEW}
        )
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)

        serialized_experiments = ExperimentSerializer(
            Experiment.objects.get_prefetched().filter(status=Experiment.STATUS_REVIEW),
            many=True,
        ).data

        self.assertEqual(serialized_experiments, json_data)


class TestExperimentDetailView(TestCase):
    def test_get_experiment_returns_experiment_info(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_variants()

        response = self.client.get(
            reverse("experiments-api-detail", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        serialized_experiment = ExperimentSerializer(experiment).data
        self.assertEqual(serialized_experiment, json_data)


class TestExperimentRecipeView(TestCase):
    @parameterized.expand(
        [
            ExperimentConstants.STATUS_SHIP,
            ExperimentConstants.STATUS_ACCEPTED,
            ExperimentConstants.STATUS_LIVE,
            ExperimentConstants.STATUS_COMPLETE,
        ]
    )
    def test_get_experiment_recipe_returns_recipe_info_for_launched_experiment(
        self, status
    ):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_status(status)

        response = self.client.get(
            reverse("experiments-api-recipe", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        serialized_experiment = ExperimentRecipeSerializer(experiment).data
        self.assertEqual(serialized_experiment, json_data)

    @parameterized.expand(
        [ExperimentConstants.STATUS_DRAFT, ExperimentConstants.STATUS_REVIEW]
    )
    def test_get_experiment_recipe_returns_404_for_not_launched_experiment(self, status):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_status(status)

        response = self.client.get(
            reverse("experiments-api-recipe", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 404)
