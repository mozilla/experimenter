from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from experimenter.experiments.tests.factories import NimbusExperimentFactory


class NimbusChangeLogsViewTest(TestCase):
    def test_render_to_response(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(slug="test-experiment")
        response = self.client.get(
            reverse(
                "nimbus-history",
                kwargs={"slug": experiment.slug},
            ),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["experiment"], experiment)
