from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from parameterized import parameterized

from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.nimbus_ui_new.views import StatusChoices
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

    def setUp(self):
        self.user = UserFactory.create(email="user@example.com")
        self.client.defaults[settings.OPENIDC_EMAIL_HEADER] = self.user.email

        for status in NimbusExperiment.Status:
            NimbusExperimentFactory.create(slug=status, status=status)

        NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            slug="review-experiment",
        )
        NimbusExperimentFactory.create(is_archived=True, slug="archived-experiment")
        NimbusExperimentFactory.create(owner=self.user, slug="my-experiment")

    def test_render_to_response(self):
        response = self.client.get(reverse("nimbus-new-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [
                e.slug
                for e in NimbusExperiment.objects.with_owner_features().filter(
                    status=NimbusExperiment.Status.LIVE.value
                )
            ],
        )
        self.assertDictEqual(
            dict(response.context["status_counts"]),
            {
                NimbusExperiment.Status.COMPLETE.value: 1,
                NimbusExperiment.Status.DRAFT.value: 2,
                NimbusExperiment.Status.LIVE.value: 1,
                NimbusExperiment.Status.PREVIEW.value: 1,
                "Review": 1,
                "Archived": 1,
                "MyExperiments": 1,
            },
        )

    @parameterized.expand(
        (
            (StatusChoices.DRAFT, ["my-experiment", NimbusExperiment.Status.DRAFT.value]),
            (StatusChoices.PREVIEW, [NimbusExperiment.Status.PREVIEW.value]),
            (StatusChoices.LIVE, [NimbusExperiment.Status.LIVE.value]),
            (StatusChoices.COMPLETE, [NimbusExperiment.Status.COMPLETE.value]),
            (StatusChoices.REVIEW, ["review-experiment"]),
            (StatusChoices.ARCHIVED, ["archived-experiment"]),
            (StatusChoices.MY_EXPERIMENTS, ["my-experiment"]),
        )
    )
    def test_filter_status(self, filter_status, expected_slugs):
        response = self.client.get(
            reverse("nimbus-new-list"),
            {"status": filter_status},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {e.slug for e in response.context["experiments"]},
            set(expected_slugs),
        )

    @patch(
        "experimenter.nimbus_ui_new.views.NimbusExperimentsListView.paginate_by", new=3
    )
    def test_pagination(self):
        for _ in range(6):
            NimbusExperimentFactory.create_with_lifecycle(
                NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING
            )
        response = self.client.get(reverse("nimbus-new-list"))
        self.assertEqual(len(response.context["experiments"]), 3)
        response = self.client.get(reverse("nimbus-new-list"), {"page": 2})
        self.assertEqual(len(response.context["experiments"]), 3)
