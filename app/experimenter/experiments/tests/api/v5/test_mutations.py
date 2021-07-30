import json

import mock
from django.conf import settings
from django.urls import reverse
from graphene_django.utils.testing import GraphQLTestCase

from experimenter.base.tests.factories import CountryFactory, LocaleFactory
from experimenter.experiments.constants.nimbus import NimbusConstants
from experimenter.experiments.models.nimbus import NimbusExperiment, NimbusFeatureConfig
from experimenter.experiments.tests.factories.nimbus import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)
from experimenter.outcomes import Outcomes
from experimenter.outcomes.tests import mock_valid_outcomes

CREATE_EXPERIMENT_MUTATION = """\
mutation($input: ExperimentInput!) {
    createExperiment(input: $input) {
        nimbusExperiment {
            slug
        }
        message
    }
}
"""


UPDATE_EXPERIMENT_MUTATION = """\
mutation($input: ExperimentInput!) {
    updateExperiment(input: $input) {
        message
    }
}
"""


@mock_valid_outcomes
class TestMutations(GraphQLTestCase):
    GRAPHQL_URL = reverse("nimbus-api-graphql")
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Outcomes.clear_cache()

    def setUp(self):
        mock_preview_task_patcher = mock.patch(
            "experimenter.experiments.api.v5.serializers."
            "nimbus_synchronize_preview_experiments_in_kinto"
        )
        self.mock_preview_task = mock_preview_task_patcher.start()
        self.addCleanup(mock_preview_task_patcher.stop)

    def test_create_experiment(self):
        user_email = "user@example.com"
        response = self.query(
            CREATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "name": "Test 1234",
                    "hypothesis": "Test hypothesis",
                    "application": NimbusExperiment.Application.DESKTOP.name,
                    "changelogMessage": "test changelog message",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        result = content["data"]["createExperiment"]
        self.assertEqual(result["message"], "success")

        experiment = NimbusExperiment.objects.first()
        self.assertEqual(experiment.name, "Test 1234")
        self.assertEqual(experiment.slug, "test-1234")
        self.assertEqual(experiment.application, NimbusExperiment.Application.DESKTOP)
        self.assertEqual(experiment.reference_branch.name, "Control")

    def test_create_experiment_error(self):
        user_email = "user@example.com"
        long_name = "test" * 1000
        response = self.query(
            CREATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "name": long_name,
                    "hypothesis": "Test hypothesis",
                    "application": NimbusExperiment.Application.DESKTOP.name,
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        result = content["data"]["createExperiment"]
        self.assertEqual(
            result["message"],
            {
                "changelog_message": ["This field is required."],
                "name": ["Ensure this field has no more than 255 characters."],
            },
        )

    def test_update_experiment_overview(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            slug="old slug",
            name="old name",
            hypothesis="old hypothesis",
            public_description="old public description",
            risk_brand=False,
            risk_revenue=False,
            risk_partner_related=False,
        )
        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "name": "new name",
                    "hypothesis": "new hypothesis",
                    "publicDescription": "new public description",
                    "changelogMessage": "test changelog message",
                    "riskBrand": True,
                    "riskRevenue": True,
                    "riskPartnerRelated": True,
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        result = content["data"]["updateExperiment"]
        self.assertEqual(result["message"], "success")

        experiment = NimbusExperiment.objects.first()
        self.assertEqual(experiment.slug, "old slug")
        self.assertEqual(experiment.name, "new name")
        self.assertEqual(experiment.hypothesis, "new hypothesis")
        self.assertEqual(experiment.public_description, "new public description")
        self.assertEqual(experiment.risk_brand, True)
        self.assertEqual(experiment.risk_revenue, True)
        self.assertEqual(experiment.risk_partner_related, True)

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
                    "hypothesis": "new hypothesis",
                    "changelogMessage": "test changelog message",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        result = content["data"]["updateExperiment"]
        self.assertEqual(
            result["message"],
            {
                "name": ["Ensure this field has no more than 255 characters."],
            },
        )

    def test_update_experiment_documentation_links(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(status=NimbusExperiment.Status.DRAFT)
        experiment_id = experiment.id

        documentation_links = [
            {
                "title": NimbusExperiment.DocumentationLink.DS_JIRA.value,
                "link": "https://example.com/bar",
            },
            {
                "title": NimbusExperiment.DocumentationLink.ENG_TICKET.value,
                "link": "https://example.com/quux",
            },
            {
                "title": NimbusExperiment.DocumentationLink.DESIGN_DOC.value,
                "link": "https://example.com/plotz",
            },
        ]

        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "documentationLinks": documentation_links,
                    "changelogMessage": "test changelog message",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

        experiment = NimbusExperiment.objects.get(id=experiment_id)
        experiment_links = experiment.documentation_links.all()
        for key in (
            "title",
            "link",
        ):
            self.assertEqual(
                {b[key] for b in documentation_links},
                {getattr(b, key) for b in experiment_links},
            )

    def test_does_not_delete_branches_when_other_fields_specified(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )
        branch_count = experiment.branches.count()
        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "name": "new name",
                    "hypothesis": "new hypothesis",
                    "publicDescription": "new public description",
                    "changelogMessage": "test changelog message",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        result = content["data"]["updateExperiment"]
        self.assertEqual(result["message"], "success")

        experiment = NimbusExperiment.objects.first()
        self.assertEqual(experiment.branches.count(), branch_count)

    def test_does_not_clear_feature_config_when_other_fields_specified(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )
        expected_feature_config = experiment.feature_config

        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "name": "new name",
                    "hypothesis": "new hypothesis",
                    "publicDescription": "new public description",
                    "changelogMessage": "test changelog message",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        result = content["data"]["updateExperiment"]
        self.assertEqual(result["message"], "success")

        experiment = NimbusExperiment.objects.first()
        self.assertEqual(experiment.feature_config, expected_feature_config)

    def test_update_experiment_branches_with_feature_config(self):
        user_email = "user@example.com"
        feature = NimbusFeatureConfigFactory(
            schema="{}", application=NimbusExperiment.Application.FENIX
        )
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.FENIX,
        )
        experiment_id = experiment.id
        reference_branch = {"name": "control", "description": "a control", "ratio": 1}
        treatment_branches = [{"name": "treatment1", "description": "desc1", "ratio": 1}]
        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "featureConfigId": feature.id,
                    "referenceBranch": reference_branch,
                    "treatmentBranches": treatment_branches,
                    "changelogMessage": "test changelog message",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)

        experiment = NimbusExperiment.objects.get(id=experiment_id)
        self.assertEqual(experiment.feature_config, feature)
        self.assertEqual(experiment.branches.count(), 2)
        self.assertEqual(experiment.reference_branch.name, reference_branch["name"])
        treatment_branch = experiment.treatment_branches[0]
        self.assertEqual(treatment_branch.name, treatment_branches[0]["name"])

    def test_update_experiment_branches_with_feature_config_error(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(status=NimbusExperiment.Status.DRAFT)
        reference_branch = {"name": "control", "description": "a control", "ratio": 1}
        treatment_branches = [{"name": "treatment1", "description": "desc1", "ratio": 1}]
        invalid_feature_config_id = (
            NimbusFeatureConfig.objects.all().order_by("-id").first().id + 1
        )
        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "featureConfigId": invalid_feature_config_id,
                    "referenceBranch": reference_branch,
                    "treatmentBranches": treatment_branches,
                    "changelogMessage": "test changelog message",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        result = content["data"]["updateExperiment"]
        self.assertEqual(
            result["message"],
            {
                "feature_config": [
                    f'Invalid pk "{invalid_feature_config_id}" - object does not exist.'
                ]
            },
        )

    def test_update_experiment_outcomes(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            primary_outcomes=[],
            secondary_outcomes=[],
        )
        outcomes = [
            o.slug for o in Outcomes.by_application(NimbusExperiment.Application.DESKTOP)
        ]
        primary_outcomes = outcomes[: NimbusExperiment.MAX_PRIMARY_OUTCOMES]
        secondary_outcomes = outcomes[NimbusExperiment.MAX_PRIMARY_OUTCOMES :]

        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "primaryOutcomes": primary_outcomes,
                    "secondaryOutcomes": secondary_outcomes,
                    "changelogMessage": "test changelog message",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)

        experiment = NimbusExperiment.objects.get(slug=experiment.slug)
        self.assertEqual(experiment.primary_outcomes, primary_outcomes)
        self.assertEqual(experiment.secondary_outcomes, secondary_outcomes)

    def test_update_experiment_outcomes_error(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            primary_outcomes=[],
            secondary_outcomes=[],
        )

        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "primaryOutcomes": ["invalid-outcome"],
                    "secondaryOutcomes": ["invalid-outcome"],
                    "changelogMessage": "test changelog message",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        result = content["data"]["updateExperiment"]
        self.assertEqual(
            result["message"],
            {
                "primary_outcomes": [
                    "Invalid choices for primary outcomes: {'invalid-outcome'}"
                ],
                "secondary_outcomes": [
                    "Invalid choices for secondary outcomes: {'invalid-outcome'}"
                ],
            },
        )

    def test_update_experiment_audience(self):
        user_email = "user@example.com"
        country = CountryFactory.create()
        locale = LocaleFactory.create()
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            application=NimbusConstants.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            population_percent=0.0,
            proposed_duration=0,
            proposed_enrollment=0,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            total_enrolled_clients=0,
        )
        self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "channel": NimbusConstants.Channel.BETA.name,
                    "firefoxMinVersion": NimbusConstants.Version.FIREFOX_83.name,
                    "populationPercent": "10",
                    "proposedDuration": 42,
                    "proposedEnrollment": 120,
                    "targetingConfigSlug": (
                        NimbusConstants.TargetingConfig.TARGETING_FIRST_RUN.name
                    ),
                    "totalEnrolledClients": 100,
                    "changelogMessage": "test changelog message",
                    "countries": [country.id],
                    "locales": [locale.id],
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.channel, NimbusConstants.Channel.BETA.value)
        self.assertEqual(
            experiment.firefox_min_version, NimbusConstants.Version.FIREFOX_83.value
        )
        self.assertEqual(experiment.population_percent, 10.0)
        self.assertEqual(experiment.proposed_duration, 42)
        self.assertEqual(experiment.proposed_enrollment, 120)
        self.assertEqual(
            experiment.targeting_config_slug,
            NimbusConstants.TargetingConfig.TARGETING_FIRST_RUN.value,
        )
        self.assertEqual(experiment.total_enrolled_clients, 100)
        self.assertEqual(list(experiment.countries.all()), [country])
        self.assertEqual(list(experiment.locales.all()), [locale])

    def test_update_experiment_audience_error(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            firefox_min_version=NimbusExperiment.Channel.NO_CHANNEL,
            population_percent=0.0,
            proposed_duration=0,
            proposed_enrollment=0,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            total_enrolled_clients=0,
        )
        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "populationPercent": "10.23471",
                    "changelogMessage": "test changelog message",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        result = content["data"]["updateExperiment"]
        self.assertEqual(
            result["message"],
            {
                "population_percent": [
                    "Ensure that there are no more than 4 decimal places."
                ]
            },
        )

    def test_update_experiment_status(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
        )
        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "status": NimbusExperiment.Status.PREVIEW.name,
                    "changelogMessage": "test changelog message",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.status, NimbusExperiment.Status.PREVIEW)

    def test_update_experiment_publish_status(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(
            publish_status=NimbusExperiment.PublishStatus.IDLE,
        )
        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "publishStatus": NimbusExperiment.PublishStatus.REVIEW.name,
                    "changelogMessage": "test changelog message",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.REVIEW)

    def test_reject_draft_experiment(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_REVIEW_REQUESTED
        )
        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "publishStatus": NimbusExperiment.PublishStatus.IDLE.name,
                    "changelogMessage": "This is not good",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)
        rejection = experiment.changes.latest_rejection()
        self.assertEqual(rejection.changed_by.email, user_email)
        self.assertEqual(rejection.message, "This is not good")

    def test_reject_ending_experiment(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_REVIEW_REQUESTED
        )
        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "publishStatus": NimbusExperiment.PublishStatus.IDLE.name,
                    "statusNext": NimbusExperiment.Status.COMPLETE.name,
                    "changelogMessage": "This is not good",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        result = content["data"]["updateExperiment"]
        self.assertEqual(result["message"], "success")

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.COMPLETE)
        rejection = experiment.changes.latest_rejection()
        self.assertEqual(rejection.changed_by.email, user_email)
        self.assertEqual(rejection.message, "This is not good")

    def test_end_experiment(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
        )
        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "publishStatus": NimbusExperiment.PublishStatus.REVIEW.name,
                    "statusNext": NimbusExperiment.Status.COMPLETE.name,
                    "changelogMessage": "test changelog message",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.REVIEW)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.COMPLETE)

    def test_end_experiment_fails_with_nonlive_status(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
        )
        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "publishStatus": NimbusExperiment.PublishStatus.REVIEW.name,
                    "statusNext": NimbusExperiment.Status.COMPLETE.name,
                    "changelogMessage": "test changelog message",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)

        content = json.loads(response.content)
        result = content["data"]["updateExperiment"]
        self.assertEqual(
            result["message"],
            {
                "status_next": [
                    "Invalid choice for status_next: 'Complete' - with status 'Draft',"
                    " the only valid choices are 'None, Live'"
                ]
            },
        )

    def test_launch_experiment_valid_with_preview_status(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.PREVIEW,
        )
        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "status": NimbusExperiment.Status.DRAFT.name,
                    "statusNext": NimbusExperiment.Status.LIVE.name,
                    "publishStatus": NimbusExperiment.PublishStatus.REVIEW.name,
                    "changelogMessage": "test changelog message",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)

        content = json.loads(response.content)
        result = content["data"]["updateExperiment"]
        self.assertEqual(result["message"], "success")

    def test_request_end_enrollment(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING
        )
        self.assertEqual(experiment.is_paused, False)
        self.assertEqual(experiment.is_paused_published, False)

        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "status": NimbusExperiment.Status.LIVE.name,
                    "statusNext": NimbusExperiment.Status.LIVE.name,
                    "publishStatus": NimbusExperiment.PublishStatus.REVIEW.name,
                    "isEnrollmentPaused": True,
                    "changelogMessage": "test changelog message",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)

        content = json.loads(response.content)
        result = content["data"]["updateExperiment"]
        self.assertEqual(result["message"], "success")

        # is_paused set to True in local DB, but is_paused_published is not yet True
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.is_paused, True)
        self.assertEqual(experiment.is_paused_published, False)

    def test_reject_end_enrollment(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_REVIEW_REQUESTED
        )
        self.assertEqual(experiment.is_paused, True)

        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "status": NimbusExperiment.Status.LIVE.name,
                    "statusNext": None,
                    "publishStatus": NimbusExperiment.PublishStatus.IDLE.name,
                    "isEnrollmentPaused": False,
                    "changelogMessage": "test changelog message",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)

        content = json.loads(response.content)
        result = content["data"]["updateExperiment"]
        self.assertEqual(result["message"], "success")

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.is_paused, False)
