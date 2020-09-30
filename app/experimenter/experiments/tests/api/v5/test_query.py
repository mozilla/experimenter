import json

from django.conf import settings
from django.urls import reverse
from graphene.utils.str_converters import to_snake_case
from graphene_django.utils.testing import GraphQLTestCase

from experimenter.experiments.models.nimbus import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory


class TestExperimentListView(GraphQLTestCase):
    GRAPHQL_URL = reverse("nimbus-api-graphql")

    def test_all_experiments(self):
        user_email = "user@example.com"
        exp = NimbusExperimentFactory.create_with_status(NimbusExperiment.Status.DRAFT)

        response = self.query(
            """
            query {
                allExperiments {
                    name
                    slug
                    publicDescription
                }
            }
            """,
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        experiments = content["data"]["allExperiments"]
        self.assertEqual(len(experiments), 1)
        for key in experiments[0]:
            self.assertEqual(experiments[0][key], str(getattr(exp, to_snake_case(key))))

    def test_experiment_by_slug(self):
        user_email = "user@example.com"
        exp = NimbusExperimentFactory.create_with_status(NimbusExperiment.Status.DRAFT)

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    name
                    slug
                    publicDescription
                }
            }
            """,
            variables={"slug": exp.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        experiment = content["data"]["experimentBySlug"]
        for key in experiment:
            self.assertEqual(experiment[key], str(getattr(exp, to_snake_case(key))))

    def test_experiment_by_slug_not_found(self):
        user_email = "user@example.com"
        NimbusExperimentFactory.create_with_status(NimbusExperiment.Status.DRAFT)

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    name
                    slug
                    publicDescription
                }
            }
            """,
            variables={"slug": "nope"},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        experiment = content["data"]["experimentBySlug"]
        self.assertIsNone(experiment)
