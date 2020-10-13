import json

from django.conf import settings
from django.urls import reverse
from graphene_django.utils.testing import GraphQLTestCase

from experimenter.experiments.models.nimbus import NimbusExperiment
from experimenter.experiments.tests.factories.nimbus import NimbusExperimentFactory

CREATE_EXPERIMENT_MUTATION = """\
mutation($input: CreateExperimentInput!) {
    createExperiment(input: $input) {
        nimbusExperiment {
            status
            name
            slug
        }
        message
        status
        clientMutationId
    }
}
"""


UPDATE_EXPERIMENT_MUTATION = """\
mutation($input: UpdateExperimentInput!) {
    updateExperiment(input: $input) {
        nimbusExperiment {
            id
            status
            name
            slug
        }
        message
        status
        clientMutationId
    }
}
"""


class TestMutations(GraphQLTestCase):
    GRAPHQL_URL = reverse("nimbus-api-graphql")

    def test_create_experiment(self):
        user_email = "user@example.com"
        response = self.query(
            CREATE_EXPERIMENT_MUTATION,
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
        self.assertEqual(result["message"], "success")
        self.assertEqual(result["status"], 200)

        exp = NimbusExperiment.objects.first()
        self.assertEqual(exp.slug, "slug1234")

    def test_create_experiment_error(self):
        user_email = "user@example.com"
        long_name = "test" * 1000
        response = self.query(
            CREATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "name": long_name,
                    "slug": "slug1234",
                    "clientMutationId": "randomid",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        result = content["data"]["createExperiment"]
        self.assertEqual(result["nimbusExperiment"], None)

        self.assertEqual(result["clientMutationId"], "randomid")
        self.assertEqual(
            result["message"],
            {"name": ["Ensure this field has no more than 255 characters."]},
        )
        self.assertEqual(result["status"], 200)

    def test_update_experiment(self):
        user_email = "user@example.com"
        exp = NimbusExperimentFactory.create_with_status(NimbusExperiment.Status.DRAFT)
        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": exp.id,
                    "name": "test1234",
                    "slug": "slug1234",
                    "clientMutationId": "randomid",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        result = content["data"]["updateExperiment"]
        experiment = result["nimbusExperiment"]
        self.assertEqual(
            experiment,
            {
                "id": f"{exp.id}",
                "status": "DRAFT",
                "name": "test1234",
                "slug": "slug1234",
            },
        )

        self.assertEqual(result["clientMutationId"], "randomid")
        self.assertEqual(result["message"], "success")
        self.assertEqual(result["status"], 200)

        exp = NimbusExperiment.objects.first()
        self.assertEqual(exp.slug, "slug1234")

    def test_update_experiment_error(self):
        user_email = "user@example.com"
        long_name = "test" * 1000
        exp = NimbusExperimentFactory.create_with_status(NimbusExperiment.Status.DRAFT)
        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": exp.id,
                    "name": long_name,
                    "slug": "slug1234",
                    "clientMutationId": "randomid",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        result = content["data"]["updateExperiment"]
        self.assertEqual(result["nimbusExperiment"], None)

        self.assertEqual(result["clientMutationId"], "randomid")
        self.assertEqual(
            result["message"],
            {"name": ["Ensure this field has no more than 255 characters."]},
        )
        self.assertEqual(result["status"], 200)
