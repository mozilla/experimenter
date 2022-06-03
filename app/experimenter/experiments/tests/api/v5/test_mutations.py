import json

import mock
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from graphene_django.utils.testing import GraphQLTestCase
from graphene_file_upload.django.testing import GraphQLFileUploadTestCase

from experimenter.base.tests.factories import (
    CountryFactory,
    LanguageFactory,
    LocaleFactory,
)
from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment, NimbusFeatureConfig
from experimenter.experiments.tests.factories import (
    TINY_PNG,
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)
from experimenter.outcomes import Outcomes
from experimenter.outcomes.tests import mock_valid_outcomes
from experimenter.targeting.constants import TargetingConstants

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

CLONE_EXPERIMENT_MUTATION = """\
mutation($input: ExperimentCloneInput!) {
    cloneExperiment(input: $input) {
        message
    }
}
"""


@mock_valid_outcomes
class TestCreateExperimentMutation(GraphQLTestCase):
    GRAPHQL_URL = reverse("nimbus-api-graphql")
    maxDiff = None

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
        self.assertIsNone(experiment.reference_branch)
        self.assertEqual(experiment.treatment_branches, [])

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
                "name": ["Ensure this field has no more than 80 characters."],
            },
        )


@mock_valid_outcomes
class TestUpdateExperimentMutationSingleFeature(
    GraphQLTestCase, GraphQLFileUploadTestCase
):
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
                    "conclusionRecommendation": "RERUN",
                    "takeawaysSummary": "the test worked",
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
        self.assertEqual(
            experiment.conclusion_recommendation,
            NimbusExperiment.ConclusionRecommendation.RERUN,
        )
        self.assertEqual(experiment.takeaways_summary, "the test worked")

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
                "name": ["Ensure this field has no more than 80 characters."],
            },
        )

    def test_update_experiment_documentation_links(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(status=NimbusExperiment.Status.DRAFT)
        experiment_id = experiment.id

        documentation_links = [
            {
                "title": NimbusExperiment.DocumentationLink.DS_JIRA,
                "link": "https://example.com/bar",
            },
            {
                "title": NimbusExperiment.DocumentationLink.ENG_TICKET,
                "link": "https://example.com/quux",
            },
            {
                "title": NimbusExperiment.DocumentationLink.DESIGN_DOC,
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
        expected_feature_config = experiment.feature_configs.get()

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
        self.assertEqual(experiment.feature_configs.get(), expected_feature_config)

    def test_update_experiment_branches_with_feature_config(self):
        user_email = "user@example.com"
        feature = NimbusFeatureConfigFactory(
            schema="{}", application=NimbusExperiment.Application.FENIX
        )
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.FENIX,
            warn_feature_schema=False,
        )
        experiment_id = experiment.id
        reference_branch_data = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "featureEnabled": False,
            "featureValue": "",
        }
        treatment_branches_data = [
            {
                "name": "treatment1",
                "description": "desc1",
                "ratio": 1,
                "featureEnabled": True,
                "featureValue": '{"key": "value"}',
            }
        ]
        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "featureConfigId": feature.id,
                    "referenceBranch": reference_branch_data,
                    "treatmentBranches": treatment_branches_data,
                    "changelogMessage": "test changelog message",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)

        experiment = NimbusExperiment.objects.get(id=experiment_id)
        self.assertEqual(experiment.feature_configs.get(), feature)
        self.assertEqual(experiment.branches.count(), 2)
        self.assertEqual(experiment.reference_branch.name, reference_branch_data["name"])
        self.assertEqual(experiment.reference_branch.feature_values.get().enabled, False)
        self.assertEqual(experiment.reference_branch.feature_values.get().value, "")
        treatment_branch = experiment.treatment_branches[0]
        self.assertEqual(treatment_branch.name, treatment_branches_data[0]["name"])
        self.assertEqual(treatment_branch.feature_values.get().enabled, True)
        self.assertEqual(
            treatment_branch.feature_values.get().value,
            treatment_branches_data[0]["featureValue"],
        )

    def test_update_experiment_warn_feature_schema(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.FENIX,
            warn_feature_schema=False,
        )
        experiment_id = experiment.id
        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "warnFeatureSchema": True,
                    "changelogMessage": "test changelog message",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)

        experiment = NimbusExperiment.objects.get(id=experiment_id)
        self.assertTrue(experiment.warn_feature_schema)

    def test_update_experiment_branches_without_feature_config(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.FENIX,
            feature_configs=[],
        )
        experiment_id = experiment.id
        reference_branch_data = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "featureEnabled": False,
            "featureValue": "",
        }
        treatment_branches_data = [
            {
                "name": "treatment1",
                "description": "desc1",
                "ratio": 1,
                "featureEnabled": True,
                "featureValue": '{"key": "value"}',
            }
        ]
        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "featureConfigId": None,
                    "referenceBranch": reference_branch_data,
                    "treatmentBranches": treatment_branches_data,
                    "changelogMessage": "test changelog message",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)

        experiment = NimbusExperiment.objects.get(id=experiment_id)
        self.assertEqual(experiment.feature_configs.count(), 0)
        self.assertEqual(experiment.branches.count(), 2)

        self.assertEqual(experiment.reference_branch.name, reference_branch_data["name"])
        self.assertEqual(
            experiment.reference_branch.feature_values.get().feature_config, None
        )
        self.assertEqual(experiment.reference_branch.feature_values.get().enabled, False)
        self.assertEqual(experiment.reference_branch.feature_values.get().value, "")

        treatment_branch = experiment.treatment_branches[0]
        self.assertEqual(treatment_branch.name, treatment_branches_data[0]["name"])
        self.assertEqual(treatment_branch.feature_values.get().feature_config, None)
        self.assertEqual(treatment_branch.feature_values.get().enabled, True)
        self.assertEqual(
            treatment_branch.feature_values.get().value,
            treatment_branches_data[0]["featureValue"],
        )

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

    def test_update_experiment_branches_with_screenshots(self):
        user_email = "user@example.com"
        feature = NimbusFeatureConfigFactory(
            schema="{}", application=NimbusExperiment.Application.FENIX
        )
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.FENIX,
        )

        reference_branch = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "screenshots": [
                {"description": "Foo", "image": None},
                {"description": "Bar", "image": None},
            ],
        }
        reference_branch_image_content_1 = TINY_PNG
        reference_branch_image_content_2 = TINY_PNG

        treatment_branches = [
            {
                "name": "treatment1",
                "description": "desc1",
                "ratio": 1,
                "screenshots": [
                    {"description": "Baz", "image": None},
                ],
            }
        ]
        treatment_branch_image_content_1 = TINY_PNG

        response = self.file_query(
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
            files={
                "input.referenceBranch.screenshots.0.image": SimpleUploadedFile(
                    name="Capture.PNG", content=reference_branch_image_content_1
                ),
                "input.referenceBranch.screenshots.1.image": SimpleUploadedFile(
                    name="Capture2.PNG", content=reference_branch_image_content_2
                ),
                "input.treatmentBranches.0.screenshots.0.image": SimpleUploadedFile(
                    name="Capture3.PNG", content=treatment_branch_image_content_1
                ),
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(
            content["data"]["updateExperiment"]["message"], "success", content
        )

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.branches.count(), 2)

        self.assertEqual(experiment.reference_branch.name, reference_branch["name"])
        self.assertEqual(experiment.reference_branch.screenshots.count(), 2)
        screenshots = experiment.reference_branch.screenshots.all()
        with screenshots[0].image.open() as image_file:
            self.assertEqual(image_file.read(), reference_branch_image_content_1)
        with screenshots[1].image.open() as image_file:
            self.assertEqual(image_file.read(), reference_branch_image_content_2)

        treatment_branch = experiment.treatment_branches[0]
        self.assertEqual(treatment_branch.name, treatment_branches[0]["name"])
        self.assertEqual(treatment_branch.screenshots.count(), 1)
        screenshots = treatment_branch.screenshots.all()
        with screenshots[0].image.open() as image_file:
            self.assertEqual(image_file.read(), treatment_branch_image_content_1)

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
        language = LanguageFactory.create()
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            application=NimbusConstants.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            firefox_max_version=NimbusExperiment.Version.NO_VERSION,
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
                    "channel": NimbusConstants.Channel.BETA.name,
                    "firefoxMinVersion": NimbusConstants.Version.FIREFOX_83.name,
                    "firefoxMaxVersion": NimbusConstants.Version.FIREFOX_95.name,
                    "populationPercent": "10",
                    "proposedDuration": 120,
                    "proposedEnrollment": 42,
                    "targetingConfigSlug": (TargetingConstants.TargetingConfig.FIRST_RUN),
                    "totalEnrolledClients": 100,
                    "changelogMessage": "test changelog message",
                    "countries": [country.id],
                    "locales": [locale.id],
                    "languages": [language.id],
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        self.assertEqual(content["data"]["updateExperiment"]["message"], "success")

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.channel, NimbusConstants.Channel.BETA)
        self.assertEqual(
            experiment.firefox_min_version, NimbusConstants.Version.FIREFOX_83
        )
        self.assertEqual(
            experiment.firefox_max_version, NimbusConstants.Version.FIREFOX_95
        )
        self.assertEqual(experiment.population_percent, 10.0)
        self.assertEqual(experiment.proposed_duration, 120)
        self.assertEqual(experiment.proposed_enrollment, 42)
        self.assertEqual(
            experiment.targeting_config_slug,
            TargetingConstants.TargetingConfig.FIRST_RUN,
        )
        self.assertEqual(experiment.total_enrolled_clients, 100)
        self.assertEqual(list(experiment.countries.all()), [country])
        self.assertEqual(list(experiment.locales.all()), [locale])
        self.assertEqual(list(experiment.languages.all()), [language])

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

    def test_update_is_archived(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_archived=False,
        )

        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "isArchived": True,
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
        self.assertTrue(experiment.is_archived)

    def test_update_conclusion_recommendation_null(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            conclusion_recommendation=NimbusExperiment.ConclusionRecommendation.FOLLOWUP,
        )
        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "conclusionRecommendation": None,
                    "takeawaysSummary": "the test worked",
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
        self.assertEqual(experiment.conclusion_recommendation, None)
        self.assertEqual(experiment.takeaways_summary, "the test worked")


@mock_valid_outcomes
class TestUpdateExperimentMutationMultiFeature(GraphQLTestCase):
    GRAPHQL_URL = reverse("nimbus-api-graphql")
    maxDiff = None

    def test_update_experiment_branches_with_feature_configs(self):
        user_email = "user@example.com"
        feature1 = NimbusFeatureConfigFactory(
            schema="{}", application=NimbusExperiment.Application.FENIX
        )
        feature2 = NimbusFeatureConfigFactory(
            schema="{}", application=NimbusExperiment.Application.FENIX
        )
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.FENIX,
            warn_feature_schema=False,
            feature_configs=[],
        )
        reference_branch_data = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "featureValues": [
                {"featureConfig": feature1.id, "enabled": False, "value": ""},
                {"featureConfig": feature2.id, "enabled": False, "value": ""},
            ],
        }
        treatment_branches_data = [
            {
                "name": "treatment1",
                "description": "desc1",
                "ratio": 1,
                "featureValues": [
                    {
                        "featureConfig": feature1.id,
                        "enabled": True,
                        "value": "{'key': 'value'}",
                    },
                    {
                        "featureConfig": feature2.id,
                        "enabled": True,
                        "value": "{'key': 'value'}",
                    },
                ],
            }
        ]
        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "featureConfigIds": [feature1.id, feature2.id],
                    "referenceBranch": reference_branch_data,
                    "treatmentBranches": treatment_branches_data,
                    "changelogMessage": "test changelog message",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(
            set(experiment.feature_configs.all().values_list("id", flat=True)),
            set([feature1.id, feature2.id]),
        )

        self.assertEqual(experiment.branches.count(), 2)

        self.assertEqual(experiment.reference_branch.name, reference_branch_data["name"])
        self.assertEqual(
            experiment.reference_branch.description, reference_branch_data["description"]
        )
        for feature_config in (feature1, feature2):
            feature_value = experiment.reference_branch.feature_values.get(
                feature_config=feature_config
            )
            self.assertEqual(feature_value.enabled, False)
            self.assertEqual(feature_value.value, "")

        treatment_branch = experiment.treatment_branches[0]
        self.assertEqual(treatment_branch.name, treatment_branches_data[0]["name"])
        self.assertEqual(
            treatment_branch.description, treatment_branches_data[0]["description"]
        )
        for feature_config in (feature1, feature2):
            feature_value = treatment_branch.feature_values.get(
                feature_config=feature_config
            )
            self.assertEqual(feature_value.enabled, True)
            self.assertEqual(feature_value.value, "{'key': 'value'}")

    def test_update_experiment_branches_without_feature_configs(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.FENIX,
            feature_configs=[],
        )
        reference_branch_data = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "featureValues": [],
        }
        treatment_branches_data = [
            {
                "name": "treatment1",
                "description": "desc1",
                "ratio": 1,
                "featureValues": [],
            }
        ]
        response = self.query(
            UPDATE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "id": experiment.id,
                    "featureConfigId": None,
                    "referenceBranch": reference_branch_data,
                    "treatmentBranches": treatment_branches_data,
                    "changelogMessage": "test changelog message",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.feature_configs.count(), 0)
        self.assertEqual(experiment.branches.count(), 2)

        self.assertEqual(experiment.reference_branch.name, reference_branch_data["name"])
        self.assertEqual(
            experiment.reference_branch.description, reference_branch_data["description"]
        )
        self.assertEqual(experiment.reference_branch.feature_values.count(), 0)

        treatment_branch = experiment.treatment_branches[0]
        self.assertEqual(treatment_branch.name, treatment_branches_data[0]["name"])
        self.assertEqual(
            treatment_branch.description, treatment_branches_data[0]["description"]
        )
        self.assertEqual(treatment_branch.feature_values.count(), 0)

    def test_update_experiment_branches_with_feature_configs_error(self):
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
                    "featureConfigIds": [invalid_feature_config_id],
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
                "feature_configs": [
                    f'Invalid pk "{invalid_feature_config_id}" - object does not exist.'
                ]
            },
        )


@mock_valid_outcomes
class TestCloneExperimentMutation(GraphQLTestCase):
    GRAPHQL_URL = reverse("nimbus-api-graphql")
    maxDiff = None

    def test_clone_experiment_success(self):
        user_email = "user@example.com"
        parent = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )
        response = self.query(
            CLONE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "parentSlug": parent.slug,
                    "name": "New Experiment",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        result = content["data"]["cloneExperiment"]
        self.assertEqual(result["message"], "success")

        child = NimbusExperiment.objects.get(slug="new-experiment")
        self.assertEqual(child.parent, parent)

    def test_clone_experiment_error_parent_slug(self):
        user_email = "user@example.com"
        response = self.query(
            CLONE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "parentSlug": "wrong slug",
                    "name": "New Experiment",
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        self.assertIn("parent_slug", content["data"]["cloneExperiment"]["message"])

    def test_clone_experiment_with_rollout_branch_slug_success(self):
        user_email = "user@example.com"
        parent = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )
        rollout_branch = parent.branches.first()
        response = self.query(
            CLONE_EXPERIMENT_MUTATION,
            variables={
                "input": {
                    "parentSlug": parent.slug,
                    "name": "New Experiment",
                    "rolloutBranchSlug": rollout_branch.slug,
                }
            },
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        result = content["data"]["cloneExperiment"]
        self.assertIsNotNone(result, f"{response.content} {rollout_branch.slug}")
        self.assertEqual(result["message"], "success", result)

        child = NimbusExperiment.objects.get(slug="new-experiment")
        self.assertEqual(child.parent, parent)
        self.assertEqual(child.branches.count(), 1)
        self.assertEqual(child.reference_branch.slug, rollout_branch.slug)
