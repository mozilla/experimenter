import json

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from parameterized import parameterized

from experimenter.experiments.api.v3.serializers import ExperimentRapidSerializer
from experimenter.experiments.models import Experiment
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.openidc.tests.factories import UserFactory
from experimenter.bugzilla.tests.mixins import MockBugzillaTasksMixin


class TestExperimentRapidViewSet(MockBugzillaTasksMixin, TestCase):
    def test_get_detail_returns_data_for_rapid_experiment(self):
        user_email = "user@example.com"

        owner = UserFactory(email=user_email)
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_RAPID,
            owner=owner,
            name="rapid experiment",
            objectives="gotta go fast",
        )

        response = self.client.get(
            reverse("experiments-rapid-detail", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)
        serialized_experiment = ExperimentRapidSerializer(experiment).data
        self.assertDictEqual(serialized_experiment, json_data)

    @parameterized.expand(
        [
            experiment_type
            for (experiment_type, _) in Experiment.TYPE_CHOICES
            if experiment_type != Experiment.TYPE_RAPID
        ]
    )
    def test_get_detail_returns_404_for_non_rapid_experiment(self, experiment_type):
        user_email = "user@example.com"

        experiment = ExperimentFactory.create(type=experiment_type)

        response = self.client.get(
            reverse("experiments-rapid-detail", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 404)

    def test_post_detail_edits_rapid_experiment(self):
        user_email = "user@example.com"
        audience = "us_only"
        features = ["picture_in_picture", "pinned_tabs"]
        firefox_min_version = Experiment.VERSION_CHOICES[0][0]

        owner = UserFactory(email=user_email)
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_RAPID,
            owner=owner,
            name="rapid experiment",
            slug="rapid-experiment",
            objectives="gotta go fast",
            audience=audience,
            features=features,
        )

        data = json.dumps(
            {
                "name": "new name",
                "objectives": "new hypothesis",
                "audience": audience,
                "features": features,
                "firefox_min_version": firefox_min_version,
                "firefox_channel": Experiment.CHANNEL_RELEASE,
            }
        )

        response = self.client.put(
            reverse("experiments-rapid-detail", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        experiment = Experiment.objects.get()
        self.assertEqual(experiment.owner.email, user_email)
        self.assertEqual(experiment.name, "new name")
        self.assertEqual(experiment.slug, "rapid-experiment")
        self.assertEqual(experiment.objectives, "new hypothesis")
        self.assertEqual(experiment.audience, audience)
        self.assertEqual(experiment.features, features)
        self.assertEqual(experiment.firefox_min_version, firefox_min_version)
        self.assertEqual(experiment.firefox_channel, Experiment.CHANNEL_RELEASE)

    def test_post_list_creates_rapid_experiment(self):
        user_email = "user@example.com"
        audience = "us_only"
        features = ["picture_in_picture", "pinned_tabs"]
        firefox_min_version = Experiment.VERSION_CHOICES[0][0]

        data = json.dumps(
            {
                "name": "rapid experiment",
                "objectives": "gotta go fast",
                "audience": audience,
                "features": features,
                "firefox_min_version": firefox_min_version,
                "firefox_channel": Experiment.CHANNEL_RELEASE,
            }
        )

        response = self.client.post(
            reverse("experiments-rapid-list"),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 201)
        experiment = Experiment.objects.get()
        self.assertEqual(experiment.owner.email, user_email)
        self.assertEqual(experiment.name, "rapid experiment")
        self.assertEqual(experiment.slug, "rapid-experiment")
        self.assertEqual(experiment.objectives, "gotta go fast")
        self.assertEqual(experiment.audience, audience)
        self.assertEqual(experiment.features, features)
        self.assertEqual(experiment.firefox_min_version, firefox_min_version)
        self.assertEqual(experiment.firefox_channel, Experiment.CHANNEL_RELEASE)

    def test_request_review_updates_status_creates_changelog(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT,
            type=Experiment.TYPE_RAPID,
            name="rapid experiment",
            slug="rapid-experiment",
            objectives="gotta go fast",
        )
        self.assertEqual(experiment.changes.count(), 1)

        response = self.client.post(
            reverse("experiments-rapid-request-review", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        experiment = Experiment.objects.get()
        self.assertEqual(experiment.status, Experiment.STATUS_REVIEW)
        self.assertEqual(experiment.changes.count(), 2)
