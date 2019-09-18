import json

from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from experimenter.experiments.models import Experiment
from experimenter.experiments.serializers import (
    ExperimentSerializer,
    ExperimentRecipeSerializer,
)
from experimenter.experiments.tests.factories import ExperimentFactory


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

    def test_get_experiment_recipe_returns_recipe_info(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_variants()

        response = self.client.get(
            reverse("experiments-api-recipe", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        serialized_experiment = ExperimentRecipeSerializer(experiment).data
        self.assertEqual(serialized_experiment, json_data)


class TestExperimentSendIntentToShipEmailView(TestCase):

    def test_put_to_view_sends_email(self):
        user_email = "user@example.com"

        experiment = ExperimentFactory.create_with_variants(
            review_intent_to_ship=False, status=Experiment.STATUS_REVIEW
        )
        old_outbox_len = len(mail.outbox)

        response = self.client.put(
            reverse(
                "experiments-api-send-intent-to-ship-email",
                kwargs={"slug": experiment.slug},
            ),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

        experiment = Experiment.objects.get(pk=experiment.pk)
        self.assertEqual(experiment.review_intent_to_ship, True)
        self.assertEqual(len(mail.outbox), old_outbox_len + 1)

    def test_put_raises_409_if_email_already_sent(self):
        experiment = ExperimentFactory.create_with_variants(
            review_intent_to_ship=True, status=Experiment.STATUS_REVIEW
        )

        response = self.client.put(
            reverse(
                "experiments-api-send-intent-to-ship-email",
                kwargs={"slug": experiment.slug},
            ),
            **{settings.OPENIDC_EMAIL_HEADER: "user@example.com"},
        )

        self.assertEqual(response.status_code, 409)


class TestExperimentCloneView(TestCase):

    def test_patch_to_view_returns_clone_name_and_url(self):
        experiment = ExperimentFactory.create(
            name="great experiment", slug="great-experiment"
        )
        user_email = "user@example.com"

        data = json.dumps({"name": "best experiment"})

        response = self.client.patch(
            reverse("experiments-api-clone", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "best experiment")
        self.assertEqual(response.json()["clone_url"], "/experiments/best-experiment/")
