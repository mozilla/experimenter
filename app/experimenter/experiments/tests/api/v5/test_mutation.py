import json

from django.conf import settings
from django.urls import reverse
from graphene_django.utils.testing import GraphQLTestCase

from experimenter.experiments.constants.nimbus import NimbusConstants
from experimenter.experiments.models.nimbus import NimbusExperiment, NimbusFeatureConfig
from experimenter.experiments.tests.factories.nimbus import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
    NimbusProbeSetFactory,
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


UPDATE_EXPERIMENT_PROBESETS_MUTATION = """\
mutation ($input: UpdateExperimentProbeSetsInput!) {
  updateExperimentProbeSets(input: $input){
    clientMutationId
    nimbusExperiment {
      id
      probeSets {
        id
        name
      }
    }
    message
    status
  }
}
"""

UPDATE_EXPERIMENT_AUDIENCE_MUTATION = """\
mutation ($input: UpdateExperimentAudienceInput!){
  updateExperimentAudience(input: $input){
    clientMutationId
    nimbusExperiment {
      id
      totalEnrolledClients
      channels
      firefoxMinVersion
      populationPercent
      proposedDuration
      proposedEnrollment
      targetingConfigSlug
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

    def test_update_experiment_probe_sets(self):
        user_email = "user@example.com"
        probe_set = NimbusProbeSetFactory()
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT, probe_sets=[]
        )
        response = self.query(
            UPDATE_EXPERIMENT_PROBESETS_MUTATION,
            variables={
                "input": {
                    "nimbusExperimentId": experiment.id,
                    "clientMutationId": "randomid",
                    "probeSetIds": [probe_set.id],
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        result = content["data"]["updateExperimentProbeSets"]
        self.assertEqual(
            result["nimbusExperiment"],
            {
                "id": str(experiment.id),
                "probeSets": [{"name": probe_set.name, "id": str(probe_set.id)}],
            },
        )
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(list(experiment.probe_sets.all()), [probe_set])

    def test_update_experiment_probe_sets_error(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT, probe_sets=[]
        )
        response = self.query(
            UPDATE_EXPERIMENT_PROBESETS_MUTATION,
            variables={
                "input": {
                    "nimbusExperimentId": experiment.id,
                    "clientMutationId": "randomid",
                    "probeSetIds": [123],
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        result = content["data"]["updateExperimentProbeSets"]
        self.assertEqual(
            result["message"],
            {"probe_sets": ['Invalid pk "123" - object does not exist.']},
        )

    def test_update_experiment_audience(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            channels=[],
            firefox_min_version=None,
            population_percent=None,
            proposed_duration=None,
            proposed_enrollment=None,
            targeting_config_slug=None,
            total_enrolled_clients=0,
        )
        response = self.query(
            UPDATE_EXPERIMENT_AUDIENCE_MUTATION,
            variables={
                "input": {
                    "nimbusExperimentId": experiment.id,
                    "clientMutationId": "randomid",
                    "channels": [NimbusConstants.Channel.DESKTOP_BETA.name],
                    "firefoxMinVersion": NimbusConstants.Version.FIREFOX_80.name,
                    "populationPercent": "10",
                    "proposedDuration": 42,
                    "proposedEnrollment": 120,
                    "targetingConfigSlug": (
                        NimbusConstants.TargetingConfig.ALL_ENGLISH.name
                    ),
                    "totalEnrolledClients": 100,
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        content = json.loads(response.content)
        result = content["data"]["updateExperimentAudience"]
        self.assertEqual(
            result["nimbusExperiment"],
            {
                "id": str(experiment.id),
                "channels": [NimbusConstants.Channel.DESKTOP_BETA.name],
                "firefoxMinVersion": NimbusConstants.Version.FIREFOX_80.name,
                "populationPercent": 10.0,
                "proposedDuration": 42,
                "proposedEnrollment": 120,
                "targetingConfigSlug": NimbusConstants.TargetingConfig.ALL_ENGLISH.name,
                "totalEnrolledClients": 100,
            },
        )
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.channels, [NimbusConstants.Channel.choices[0][0]])
        self.assertEqual(
            experiment.firefox_min_version, NimbusConstants.Version.choices[0][0]
        )
        self.assertEqual(experiment.population_percent, 10.0)
        self.assertEqual(experiment.proposed_duration, 42)
        self.assertEqual(experiment.proposed_enrollment, 120)
        self.assertEqual(
            experiment.targeting_config_slug,
            NimbusConstants.TargetingConfig.ALL_ENGLISH.value,
        )
        self.assertEqual(experiment.total_enrolled_clients, 100)

    def test_update_experiment_audience_error(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            channels=[],
            firefox_min_version=None,
            population_percent=None,
            proposed_duration=None,
            proposed_enrollment=None,
            targeting_config_slug=None,
            total_enrolled_clients=0,
        )
        response = self.query(
            UPDATE_EXPERIMENT_AUDIENCE_MUTATION,
            variables={
                "input": {
                    "nimbusExperimentId": experiment.id,
                    "clientMutationId": "randomid",
                    "populationPercent": "10.23471",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        result = content["data"]["updateExperimentAudience"]
        self.assertEqual(
            result["message"],
            {
                "population_percent": [
                    "Ensure that there are no more than 4 decimal places."
                ]
            },
        )
