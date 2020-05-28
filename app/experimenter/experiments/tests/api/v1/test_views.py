import json

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from parameterized import parameterized
from rest_framework_csv.renderers import CSVRenderer

from experimenter.experiments.constants import ExperimentConstants
from experimenter.experiments.models import Experiment
from experimenter.experiments.api.v1.serializers import (
    ExperimentSerializer,
    ExperimentCSVSerializer,
)
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.normandy.serializers import ExperimentRecipeSerializer
from experimenter.openidc.tests.factories import UserFactory
from experimenter.projects.tests.factories import ProjectFactory


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
            Experiment.objects.all(), many=True
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
            Experiment.objects.filter(status=Experiment.STATUS_REVIEW), many=True
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


class TestExperimentCSVListView(TestCase):
    def test_get_returns_csv_info(self):
        user_email = "user@example.com"
        experiment1 = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="a"
        )
        experiment2 = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="b"
        )

        response = self.client.get(
            reverse("experiments-api-csv"), **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

        csv_data = response.content
        expected_csv_data = CSVRenderer().render(
            ExperimentCSVSerializer([experiment1, experiment2], many=True).data,
            renderer_context={"header": ExperimentCSVSerializer.Meta.fields},
        )
        self.assertEqual(csv_data, expected_csv_data)

    def test_view_filters_by_project(self):
        user_email = "user@example.com"
        project = ProjectFactory.create()
        experiment1 = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="a", projects=[project]
        )
        experiment2 = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="b", projects=[project]
        )
        ExperimentFactory.create_with_variants()

        url = reverse("experiments-api-csv")
        response = self.client.get(
            f"{url}?projects={project.id}", **{settings.OPENIDC_EMAIL_HEADER: user_email}
        )

        self.assertEqual(response.status_code, 200)

        csv_data = response.content
        expected_csv_data = CSVRenderer().render(
            ExperimentCSVSerializer([experiment1, experiment2], many=True).data,
            renderer_context={"header": ExperimentCSVSerializer.Meta.fields},
        )
        self.assertEqual(csv_data, expected_csv_data)

    def test_view_filters_by_subscriber(self):
        user = UserFactory(email="user@example.com")
        experiment1 = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="a"
        )
        experiment1.subscribers.add(user)
        experiment2 = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="b"
        )
        experiment2.subscribers.add(user)
        ExperimentFactory.create_with_variants()

        url = reverse("experiments-api-csv")
        response = self.client.get(
            f"{url}?subscribed=on", **{settings.OPENIDC_EMAIL_HEADER: user.email}
        )

        self.assertEqual(response.status_code, 200)

        csv_data = response.content
        expected_csv_data = CSVRenderer().render(
            ExperimentCSVSerializer([experiment1, experiment2], many=True).data,
            renderer_context={"header": ExperimentCSVSerializer.Meta.fields},
        )
        self.assertEqual(csv_data, expected_csv_data)
