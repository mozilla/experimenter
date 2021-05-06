import datetime
import json

from django.conf import settings
from django.urls import reverse
from graphene.utils.str_converters import to_snake_case
from graphene_django.utils.testing import GraphQLTestCase

from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.models.nimbus import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.experiments.tests.factories.nimbus import NimbusFeatureConfigFactory
from experimenter.outcomes import Outcomes


class TestNimbusQuery(GraphQLTestCase):
    GRAPHQL_URL = reverse("nimbus-api-graphql")

    def test_experiments(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED
        )

        response = self.query(
            """
            query {
                experiments {
                    name
                    slug
                    publicDescription
                    riskMitigationLink
                }
            }
            """,
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        experiments = content["data"]["experiments"]
        self.assertEqual(len(experiments), 1)
        for key in experiments[0]:
            self.assertEqual(
                experiments[0][key], str(getattr(experiment, to_snake_case(key)))
            )

    def test_experiments_with_no_branches_returns_empty_values(self):
        user_email = "user@example.com"
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED, branches=[]
        )

        response = self.query(
            """
            query {
                experiments {
                    referenceBranch {
                        name
                        slug
                        description
                        ratio
                    }
                    treatmentBranches {
                        name
                        slug
                        description
                        ratio
                    }
                }
            }
            """,
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        experiment_data = content["data"]["experiments"][0]
        self.assertEqual(
            experiment_data["referenceBranch"],
            {"name": "", "slug": "", "description": "", "ratio": 1},
        )
        self.assertEqual(
            experiment_data["treatmentBranches"],
            [{"name": "", "slug": "", "description": "", "ratio": 1}],
        )

    def test_experiments_with_branches_returns_branch_data(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED
        )

        response = self.query(
            """
            query {
                experiments {
                    referenceBranch {
                        slug
                    }
                    treatmentBranches {
                        slug
                    }
                }
            }
            """,
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        experiment_data = content["data"]["experiments"][0]
        self.assertEqual(
            experiment_data["referenceBranch"],
            {"slug": experiment.reference_branch.slug},
        )
        self.assertEqual(
            {b["slug"] for b in experiment_data["treatmentBranches"]},
            {b.slug for b in experiment.treatment_branches},
        )

    def test_experiments_with_documentation_links_return_link_data(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED
        )
        documentation_links = experiment.documentation_links.all()
        self.assert_(len(documentation_links) > 0)

        response = self.query(
            """
            query {
                experiments {
                    documentationLinks {
                        title
                        link
                    }
                }
            }
            """,
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        experiment_data = content["data"]["experiments"][0]
        for key in (
            "title",
            "link",
        ):
            self.assertEqual(
                {b[key] for b in experiment_data["documentationLinks"]},
                {getattr(b, key) for b in documentation_links},
            )

    def test_experiment_returns_publish_status(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create(
            publish_status=NimbusExperiment.PublishStatus.IDLE
        )

        response = self.query(
            """
            query {
                experiments {
                    publishStatus
                }
            }
            """,
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        experiment_data = content["data"]["experiments"][0]
        self.assertEqual(
            experiment_data["publishStatus"],
            experiment.publish_status.name,
        )

    def test_experiment_by_slug_ready_for_review(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED
        )

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    name
                    slug
                    publicDescription
                    readyForReview {
                        message
                        ready
                    }
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiment_data = content["data"]["experimentBySlug"]
        self.assertEqual(experiment_data["name"], experiment.name)
        self.assertEqual(experiment_data["slug"], experiment.slug)
        self.assertEqual(
            experiment_data["publicDescription"], experiment.public_description
        )
        self.assertEqual(
            experiment_data["readyForReview"], {"message": {}, "ready": True}
        )

    def test_experiment_by_slug_not_ready_for_review(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
            hypothesis=NimbusExperiment.HYPOTHESIS_DEFAULT,
        )

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    readyForReview {
                        message
                        ready
                    }
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiment_data = content["data"]["experimentBySlug"]
        self.assertEqual(
            experiment_data["readyForReview"],
            {
                "message": {"hypothesis": ["Hypothesis cannot be the default value."]},
                "ready": False,
            },
        )

    def test_experiment_by_slug_not_found(self):
        user_email = "user@example.com"
        NimbusExperimentFactory.create_with_lifecycle(NimbusExperiment.Lifecycles.CREATED)

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

    def test_experiment_jexl_targeting_expression(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
            targeting_config_slug=NimbusExperiment.TargetingConfig.ALL_ENGLISH,
            application=NimbusExperiment.Application.DESKTOP,
        )
        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    jexlTargetingExpression
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiment_data = content["data"]["experimentBySlug"]
        self.assertEqual(experiment_data["jexlTargetingExpression"], experiment.targeting)

    def test_experiment_no_jexl_targeting_expression(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
            targeting_config_slug="",
            application=NimbusExperiment.Application.FENIX,
        )
        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    jexlTargetingExpression
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiment_data = content["data"]["experimentBySlug"]
        self.assertEqual(
            experiment_data["jexlTargetingExpression"],
            "true",
        )

    def test_experiment_computed_end_date_proposed(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_duration=10,
        )
        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    computedEndDate
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiment_data = content["data"]["experimentBySlug"]
        self.assertEqual(
            experiment_data["computedEndDate"],
            experiment.proposed_end_date.isoformat(),
        )

    def test_experiment_computed_end_date_actual(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.ENDING_APPROVE_APPROVE
        )
        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    computedEndDate
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiment_data = content["data"]["experimentBySlug"]
        self.assertEqual(
            experiment_data["computedEndDate"],
            experiment.end_date.isoformat(),
        )

    def test_experiment_in_review_can_review(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_REVIEW_REQUESTED
        )
        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    canReview
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiment_data = content["data"]["experimentBySlug"]
        self.assertTrue(experiment_data["canReview"])

    def test_experiment_no_rejection_data(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED
        )

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    rejection {
                        changedBy {
                            email
                        }
                    }
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiment_data = content["data"]["experimentBySlug"]
        self.assertIsNone(experiment_data["rejection"])

    def test_experiment_with_rejection(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_REJECT
        )
        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    rejection {
                        changedBy {
                            email
                        }
                    }
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiment_data = content["data"]["experimentBySlug"]
        self.assertEqual(
            experiment_data["rejection"]["changedBy"]["email"], experiment.owner.email
        )

    def test_experiment_no_review_request_data(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED
        )

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    reviewRequest {
                        changedBy {
                            email
                        }
                    }
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiment_data = content["data"]["experimentBySlug"]
        self.assertIsNone(experiment_data["reviewRequest"])

    def test_experiment_with_review_request(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_REVIEW_REQUESTED
        )
        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    reviewRequest {
                        changedBy {
                            email
                        }
                    }
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiment_data = content["data"]["experimentBySlug"]
        self.assertEqual(
            experiment_data["reviewRequest"]["changedBy"]["email"], experiment.owner.email
        )

    def test_experiment_without_timeout_returns_none(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_WAITING
        )
        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    timeout {
                        changedBy {
                            email
                        }
                    }
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        experiment_data = content["data"]["experimentBySlug"]
        self.assertIsNone(experiment_data["timeout"])

    def test_experiment_with_timeout_returns_changelog(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_TIMEOUT
        )
        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    timeout {
                        changedBy {
                            email
                        }
                    }
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        experiment_data = content["data"]["experimentBySlug"]
        self.assertEqual(
            experiment_data["timeout"]["changedBy"]["email"], experiment.owner.email
        )

    def test_recipe_json_returns_serialized_data(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED
        )
        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    recipeJson
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        experiment_data = content["data"]["experimentBySlug"]
        self.assertEqual(
            experiment_data["recipeJson"],
            json.dumps(
                NimbusExperimentSerializer(experiment).data, indent=2, sort_keys=True
            ),
        )

    def test_nimbus_config(self):
        user_email = "user@example.com"
        feature_configs = NimbusFeatureConfigFactory.create_batch(10)

        response = self.query(
            """
            query{
                nimbusConfig{
                    application {
                        label
                        value
                    }
                    channel {
                        label
                        value
                    }
                    firefoxMinVersion {
                        label
                        value
                    }
                    featureConfig {
                        name
                        slug
                        id
                        description
                    }
                    outcomes {
                        friendlyName
                        slug
                        application
                        description
                    }
                    targetingConfigSlug {
                        label
                        value
                    }
                    documentationLink {
                        label
                        value
                    }
                    hypothesisDefault
                    maxPrimaryOutcomes
                    kintoAdminUrl
                }
            }
            """,
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        config = content["data"]["nimbusConfig"]

        def assertChoices(data, text_choices):
            self.assertEqual(len(data), len(text_choices.names))
            for index, name in enumerate(text_choices.names):
                self.assertEqual(data[index]["label"], text_choices[name].label)
                self.assertEqual(data[index]["value"], name)

        assertChoices(config["application"], NimbusExperiment.Application)
        assertChoices(config["channel"], NimbusExperiment.Channel)
        assertChoices(config["firefoxMinVersion"], NimbusExperiment.Version)
        assertChoices(config["targetingConfigSlug"], NimbusExperiment.TargetingConfig)
        assertChoices(config["documentationLink"], NimbusExperiment.DocumentationLink)
        self.assertEqual(config["kintoAdminUrl"], settings.KINTO_ADMIN_URL)
        self.assertEqual(len(config["featureConfig"]), 13)

        for outcome in Outcomes.all():
            self.assertIn(
                {
                    "slug": outcome.slug,
                    "friendlyName": outcome.friendly_name,
                    "application": NimbusExperiment.Application(outcome.application).name,
                    "description": outcome.description,
                },
                config["outcomes"],
            )

        for feature_config in feature_configs:
            config_feature_config = next(
                filter(lambda f: f["id"] == feature_config.id, config["featureConfig"])
            )
            self.assertEqual(config_feature_config["id"], feature_config.id)
            self.assertEqual(config_feature_config["name"], feature_config.name)
            self.assertEqual(config_feature_config["slug"], feature_config.slug)
            self.assertEqual(
                config_feature_config["description"], feature_config.description
            )

        self.assertEqual(config["hypothesisDefault"], NimbusExperiment.HYPOTHESIS_DEFAULT)
        self.assertEqual(
            config["maxPrimaryOutcomes"], NimbusExperiment.MAX_PRIMARY_OUTCOMES
        )

    def test_paused_experiment_returns_date(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.LAUNCH_APPROVE_APPROVE,
            is_paused=True,
            proposed_enrollment=7,
        )
        live_change = experiment.changes.get(
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
        )
        live_change.changed_on = datetime.datetime(2021, 1, 1)
        live_change.save()

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    isEnrollmentPaused
                    enrollmentEndDate
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiment_data = content["data"]["experimentBySlug"]
        self.assertEqual(experiment_data["isEnrollmentPaused"], True)
        self.assertEqual(experiment_data["enrollmentEndDate"], "2021-01-08")

    def test_signoff_recommendations(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
            risk_brand=True,
            risk_revenue=True,
            risk_partner_related=True,
        )

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    signoffRecommendations {
                        qaSignoff
                        vpSignoff
                        legalSignoff
                    }
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiment_data = content["data"]["experimentBySlug"]
        self.assertEqual(experiment_data["signoffRecommendations"]["qaSignoff"], True)
        self.assertEqual(experiment_data["signoffRecommendations"]["vpSignoff"], True)
        self.assertEqual(experiment_data["signoffRecommendations"]["legalSignoff"], True)
