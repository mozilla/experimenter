from django.test import RequestFactory, TestCase
from django.urls import reverse

from experimenter.changelog.views import NimbusChangeLogsView
from experimenter.experiments.tests.factories import (
    NimbusChangeLogFactory,
    NimbusExperimentFactory,
)
from experimenter.openidc.tests.factories import UserFactory


class NimbusChangeLogsViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserFactory.create()
        self.experiment = NimbusExperimentFactory.create(slug="test-experiment")
        self.changelog1 = NimbusChangeLogFactory.create(
            experiment=self.experiment, message="Change log 1"
        )
        self.changelog2 = NimbusChangeLogFactory.create(
            experiment=self.experiment, message="Change log 2"
        )
        self.view = NimbusChangeLogsView.as_view()

    def test_render_to_response(self):
        request = self.factory.get(
            reverse("changelogs-by-slug", kwargs={"slug": self.experiment.slug})
        )
        request.user = self.user
        response = self.view(request, slug=self.experiment.slug)
        self.assertEqual(response.status_code, 200)

    def test_get_context_data(self):
        request = self.factory.get(
            reverse("changelogs-by-slug", kwargs={"slug": self.experiment.slug})
        )
        request.user = self.user
        response = self.view(request, slug=self.experiment.slug)
        context = response.context_data
        self.assertEqual(context["experiment"], self.experiment)
