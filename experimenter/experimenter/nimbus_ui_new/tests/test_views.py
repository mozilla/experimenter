from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.openidc.tests.factories import UserFactory


class NimbusChangeLogsViewTest(TestCase):
    def test_render_to_response(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(slug="test-experiment")
        response = self.client.get(
            reverse(
                "nimbus-new-history",
                kwargs={"slug": experiment.slug},
            ),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["experiment"], experiment)


class NimbusExperimentsListViewTest(TestCase):
    maxDiff = None

    def test_render_to_response(self):
        user_email = "user@example.com"
        for status in NimbusExperiment.Status:
            NimbusExperimentFactory.create(slug=status, status=status)

        NimbusExperimentFactory.create(
            publish_status=NimbusExperiment.PublishStatus.REVIEW
        )
        NimbusExperimentFactory.create(is_archived=True)
        NimbusExperimentFactory.create(owner=UserFactory.create(email=user_email))

        response = self.client.get(
            reverse("nimbus-new-list"),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [e.slug for e in NimbusExperiment.objects.with_owner_features()],
        )
        self.assertDictEqual(
            dict(response.context["status_counts"]),
            {
                NimbusExperiment.Status.COMPLETE.value: 1,
                NimbusExperiment.Status.DRAFT.value: 4,
                NimbusExperiment.Status.LIVE.value: 1,
                NimbusExperiment.Status.PREVIEW.value: 1,
                "Review": 1,
                "Archived": 1,
                "MyExperiments": 1,
            },
        )
