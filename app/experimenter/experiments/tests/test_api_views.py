import json

from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from experimenter.experiments.models import Experiment
from experimenter.experiments.serializers import ExperimentSerializer
from experimenter.experiments.tests.factories import ExperimentFactory
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

    def test_list_view_filters_by_project_slug(self):
        project = ProjectFactory.create()
        project_experiments = []

        # another projects experiments should be excluded
        for i in range(2):
            ExperimentFactory.create_with_variants()

        # started project experiments should be included
        for i in range(3):
            experiment = ExperimentFactory.create_with_variants(
                project=project
            )
            project_experiments.append(experiment)

        response = self.client.get(
            reverse("experiments-api-list"), {"project__slug": project.slug}
        )
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)

        serialized_experiments = ExperimentSerializer(
            project.experiments.all(), many=True
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
            reverse("experiments-api-list"),
            {"status": Experiment.STATUS_REVIEW},
        )
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)

        serialized_experiments = ExperimentSerializer(
            Experiment.objects.filter(status=Experiment.STATUS_REVIEW),
            many=True,
        ).data

        self.assertEqual(serialized_experiments, json_data)


class TestExperimentDetailView(TestCase):

    def test_get_experiment_returns_experiment_info(self):
        user_email = "user@example.com"

        experiment = ExperimentFactory.create_with_variants()

        response = self.client.get(
            reverse(
                "experiments-api-detail", kwargs={"slug": experiment.slug}
            ),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)

        serialized_experiment = ExperimentSerializer(experiment).data

        self.assertEqual(serialized_experiment, json_data)


class TestExperimentAcceptView(TestCase):

    def test_post_to_accept_view_sets_status_accepted(self):
        user_email = "user@example.com"

        experiment = ExperimentFactory.create_with_variants()
        experiment.status = experiment.STATUS_REVIEW
        experiment.save()

        response = self.client.patch(
            reverse(
                "experiments-api-accept", kwargs={"slug": experiment.slug}
            ),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

        experiment = Experiment.objects.get(pk=experiment.pk)
        self.assertEqual(experiment.status, experiment.STATUS_ACCEPTED)

        change = experiment.changes.get()
        self.assertEqual(change.old_status, experiment.STATUS_REVIEW)
        self.assertEqual(change.new_status, experiment.STATUS_ACCEPTED)
        self.assertEqual(change.changed_by.email, user_email)

    def test_post_to_accept_raises_404_for_non_pending_experiment(self):
        experiment = ExperimentFactory.create_with_variants()

        response = self.client.patch(
            reverse(
                "experiments-api-accept", kwargs={"slug": experiment.slug}
            ),
            **{settings.OPENIDC_EMAIL_HEADER: "user@example.com"},
        )

        self.assertEqual(response.status_code, 404)


class TestExperimentRejectView(TestCase):

    def test_post_to_reject_view_sets_status_rejected(self):
        user_email = "user@example.com"
        rejection_message = "This experiment was rejected for reasons."

        experiment = ExperimentFactory.create_with_variants()
        experiment.status = experiment.STATUS_REVIEW
        experiment.save()

        response = self.client.patch(
            reverse(
                "experiments-api-reject", kwargs={"slug": experiment.slug}
            ),
            data=json.dumps({"message": rejection_message}),
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

        experiment = Experiment.objects.get(pk=experiment.pk)
        self.assertEqual(experiment.status, experiment.STATUS_REJECTED)

        change = experiment.changes.get()
        self.assertEqual(change.old_status, experiment.STATUS_REVIEW)
        self.assertEqual(change.new_status, experiment.STATUS_REJECTED)
        self.assertEqual(change.changed_by.email, user_email)
        self.assertEqual(change.message, rejection_message)

    def test_post_to_reject_raises_404_for_non_pending_experiment(self):
        experiment = ExperimentFactory.create_with_variants()

        response = self.client.patch(
            reverse(
                "experiments-api-reject", kwargs={"slug": experiment.slug}
            ),
            **{settings.OPENIDC_EMAIL_HEADER: "user@example.com"},
        )

        self.assertEqual(response.status_code, 404)


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
