import json

from django.conf import settings
from django.urls import reverse
from graphene_django.utils.testing import GraphQLTestCase

from experimenter.experiments.models.nimbus import NimbusExperiment, NimbusFeatureConfig
from experimenter.experiments.tests.factories.nimbus import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)

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


UPDATE_EXPERIMENT_BRANCHES_MUTATION = """\
mutation ($input: UpdateExperimentBranchesInput !) {
  updateExperimentBranches(input: $input){
    clientMutationId
    nimbusExperiment {
      id
      featureConfig {
        name
      }
      status
      name
      slug
      controlBranch {
        name
        description
        ratio
      }
      treatmentBranches {
        name
        description
        ratio
      }
    }
    message
    status
  }
}
"""


class TestMutations(GraphQLTestCase):
    GRAPHQL_URL = reverse("nimbus-api-graphql")
    maxDiff = None

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
        experiment = NimbusExperimentFactory.create(status=NimbusExperiment.Status.DRAFT)
        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
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
        experiment_result = result["nimbusExperiment"]
        self.assertEqual(
            experiment_result,
            {
                "id": f"{experiment.id}",
                "status": "DRAFT",
                "name": "test1234",
                "slug": "slug1234",
            },
        )

        self.assertEqual(result["clientMutationId"], "randomid")
        self.assertEqual(result["message"], "success")
        self.assertEqual(result["status"], 200)

        experiment = NimbusExperiment.objects.first()
        self.assertEqual(experiment.slug, "slug1234")

    def test_update_experiment_error(self):
        user_email = "user@example.com"
        long_name = "test" * 1000
        experiment = NimbusExperimentFactory.create(status=NimbusExperiment.Status.DRAFT)
        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
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

    def test_update_experiment_branches_with_feature_config(self):
        user_email = "user@example.com"
        feature = NimbusFeatureConfigFactory()
        experiment = NimbusExperimentFactory.create(status=NimbusExperiment.Status.DRAFT)
        experiment_id = experiment.id
        control_branch = {"name": "control", "description": "a control", "ratio": 1}
        treatment_branches = [{"name": "treatment1", "description": "desc1", "ratio": 1}]
        response = self.query(
            UPDATE_EXPERIMENT_BRANCHES_MUTATION,
            variables={
                "input": {
                    "nimbusExperimentId": experiment.id,
                    "featureConfigId": feature.id,
                    "clientMutationId": "randomid",
                    "controlBranch": control_branch,
                    "treatmentBranches": treatment_branches,
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        result = content["data"]["updateExperimentBranches"]
        self.assertEqual(
            result["nimbusExperiment"],
            {
                "id": str(experiment.id),
                "featureConfig": {"name": feature.name},
                "status": experiment.status.upper(),
                "name": experiment.name,
                "slug": experiment.slug,
                "controlBranch": control_branch,
                "treatmentBranches": treatment_branches,
            },
        )
        experiment = NimbusExperiment.objects.get(id=experiment_id)
        self.assertEqual(experiment.feature_config, feature)
        self.assertEqual(experiment.branches.count(), 2)
        self.assertEqual(experiment.control_branch.name, control_branch["name"])
        treatment_branch = experiment.treatment_branches[0]
        self.assertEqual(treatment_branch.name, treatment_branches[0]["name"])

    def test_update_experiment_branches_with_feature_config_error(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(status=NimbusExperiment.Status.DRAFT)
        control_branch = {"name": "control", "description": "a control", "ratio": 1}
        treatment_branches = [{"name": "treatment1", "description": "desc1", "ratio": 1}]
        # The NimbusExperimentFactory always creates a single feature config.
        self.assertEqual(NimbusFeatureConfig.objects.count(), 1)
        response = self.query(
            UPDATE_EXPERIMENT_BRANCHES_MUTATION,
            variables={
                "input": {
                    "nimbusExperimentId": experiment.id,
                    "featureConfigId": 2,
                    "clientMutationId": "randomid",
                    "controlBranch": control_branch,
                    "treatmentBranches": treatment_branches,
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        result = content["data"]["updateExperimentBranches"]
        self.assertEqual(
            result["message"],
            {"feature_config": ['Invalid pk "2" - object does not exist.']},
        )
