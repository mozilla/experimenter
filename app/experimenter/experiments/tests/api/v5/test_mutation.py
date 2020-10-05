import json

from django.conf import settings
from django.urls import reverse
from graphene_django.utils.testing import GraphQLTestCase

from experimenter.experiments.models.nimbus import NimbusExperiment


class TestCreateExperiment(GraphQLTestCase):
    GRAPHQL_URL = reverse("nimbus-api-graphql")

    def test_create_experiment(self):
        user_email = "user@example.com"
        response = self.query(
            """
            mutation($input: CreateExperimentMutationInput!) {
                createExperiment(input: $input) {
                    nimbusExperiment {
                        status
                        name
                        slug
                    }
                    errors {
                        field
                        messages
                    }
                    clientMutationId
                }
            }
            """,
            variables={
                "input": {
                    "name": "test1234",
                    "slug": "slug1234",
                    "clientMutationId": "randomid",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        result = content["data"]["createExperiment"]
        experiment = result["nimbusExperiment"]
        self.assertEqual(
            experiment, {"status": "DRAFT", "name": "test1234", "slug": "slug1234"}
        )

        self.assertEqual(result["clientMutationId"], "randomid")

        errors = result["errors"]
        self.assertEqual(errors, [])

        exp = NimbusExperiment.objects.first()
        self.assertEqual(exp.slug, "slug1234")
