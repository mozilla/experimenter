import datetime
import json

from django.conf import settings
from django.urls import reverse
from graphene_django.utils.testing import GraphQLTestCase
from parameterized import parameterized

from experimenter.base.models import Country, Language, Locale
from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.models.nimbus import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.experiments.tests.factories.nimbus import NimbusFeatureConfigFactory
from experimenter.outcomes import Outcomes


class TestNimbusExperimentsQuery(GraphQLTestCase):
    GRAPHQL_URL = reverse("nimbus-api-graphql")
    maxDiff = None

    def test_experiments(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )

        response = self.query(
            """
            query {
                experiments {
                    isArchived
                    canEdit
                    canArchive
                    name
                    slug
                    publicDescription
                    riskMitigationLink
                    warnFeatureSchema
                }
            }
            """,
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        experiments = content["data"]["experiments"]
        self.assertEqual(len(experiments), 1)
        experiment_data = experiments[0]
        self.assertEqual(experiment_data["isArchived"], experiment.is_archived)
        self.assertEqual(experiment_data["canArchive"], experiment.can_archive)
        self.assertEqual(experiment_data["name"], experiment.name)
        self.assertEqual(experiment_data["slug"], experiment.slug)
        self.assertEqual(
            experiment_data["publicDescription"], experiment.public_description
        )
        self.assertEqual(
            experiment_data["riskMitigationLink"], experiment.risk_mitigation_link
        )
        self.assertEqual(experiment_data["canEdit"], experiment.can_edit)
        self.assertEqual(
            experiment_data["warnFeatureSchema"],
            experiment.warn_feature_schema,
        )

    def test_experiments_with_no_branches_returns_empty_reference_treatment_values(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )
        experiment.delete_branches()

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
            {"name": "Control", "slug": "", "description": "", "ratio": 1},
        )
        self.assertEqual(
            experiment_data["treatmentBranches"],
            [{"name": "Treatment A", "slug": "", "description": "", "ratio": 1}],
        )

    def test_experiments_with_branches_returns_branch_data_single_feature(self):
        user_email = "user@example.com"
        feature_config = NimbusFeatureConfigFactory(
            application=NimbusExperiment.Application.DESKTOP
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED, feature_configs=[feature_config]
        )
        screenshot = experiment.reference_branch.screenshots.first()
        screenshot.image = None
        screenshot.save()

        response = self.query(
            """
            query {
                experiments {
                    featureConfig {
                        id
                        name
                    }
                    referenceBranch {
                        slug
                        name
                        description
                        ratio
                        featureEnabled
                        featureValue
                        screenshots {
                            description
                            image
                        }
                    }
                    treatmentBranches {
                        slug
                        name
                        description
                        ratio
                        featureEnabled
                        featureValue
                        screenshots {
                            description
                            image
                        }
                    }
                }
            }
            """,
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiment_data = content["data"]["experiments"][0]

        self.assertEqual(
            experiment_data["featureConfig"],
            {"id": feature_config.id, "name": feature_config.name},
        )

        self.assertEqual(
            experiment_data["referenceBranch"],
            {
                "slug": experiment.reference_branch.slug,
                "name": experiment.reference_branch.name,
                "description": experiment.reference_branch.description,
                "ratio": experiment.reference_branch.ratio,
                "featureEnabled": (
                    experiment.reference_branch.feature_values.get().enabled
                ),
                "featureValue": experiment.reference_branch.feature_values.get().value,
                "screenshots": [{"description": screenshot.description, "image": None}],
            },
        )

        for treatment_branch_data in experiment_data["treatmentBranches"]:
            treatment_branch = experiment.branches.get(slug=treatment_branch_data["slug"])
            self.assertEqual(
                treatment_branch_data,
                {
                    "slug": treatment_branch.slug,
                    "name": treatment_branch.name,
                    "description": treatment_branch.description,
                    "ratio": treatment_branch.ratio,
                    "featureEnabled": treatment_branch.feature_values.get().enabled,
                    "featureValue": treatment_branch.feature_values.get().value,
                    "screenshots": [
                        {"description": s.description, "image": s.image.url}
                        for s in treatment_branch.screenshots.all()
                    ],
                },
            )

    def test_experiments_with_branches_returns_branch_data_multi_feature(self):
        user_email = "user@example.com"
        feature_config1 = NimbusFeatureConfigFactory(
            application=NimbusExperiment.Application.DESKTOP
        )
        feature_config2 = NimbusFeatureConfigFactory(
            application=NimbusExperiment.Application.DESKTOP
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config1, feature_config2],
        )
        screenshot = experiment.reference_branch.screenshots.first()
        screenshot.image = None
        screenshot.save()

        response = self.query(
            """
            query {
                experiments {
                    featureConfigs {
                        id
                        name
                    }
                    referenceBranch {
                        slug
                        name
                        description
                        ratio
                        featureValues {
                            featureConfig {
                                id
                            }
                            enabled
                            value
                        }
                        screenshots {
                            description
                            image
                        }
                    }
                    treatmentBranches {
                        slug
                        name
                        description
                        ratio
                        featureValues {
                            featureConfig {
                                id
                            }
                            enabled
                            value
                        }
                        screenshots {
                            description
                            image
                        }
                    }
                }
            }
            """,
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiment_data = content["data"]["experiments"][0]

        for feature_config in (feature_config1, feature_config2):
            self.assertIn(
                {"id": feature_config.id, "name": feature_config.name},
                experiment_data["featureConfigs"],
            )

        reference_branch_feature_values_data = experiment_data["referenceBranch"].pop(
            "featureValues"
        )
        for (
            reference_branch_feature_value
        ) in experiment.reference_branch.feature_values.all():
            self.assertIn(
                {
                    "featureConfig": {
                        "id": reference_branch_feature_value.feature_config.id
                    },
                    "enabled": reference_branch_feature_value.enabled,
                    "value": reference_branch_feature_value.value,
                },
                reference_branch_feature_values_data,
            )

        self.assertEqual(
            experiment_data["referenceBranch"],
            {
                "slug": experiment.reference_branch.slug,
                "name": experiment.reference_branch.name,
                "description": experiment.reference_branch.description,
                "ratio": experiment.reference_branch.ratio,
                "screenshots": [{"description": screenshot.description, "image": None}],
            },
        )

        for treatment_branch_data in experiment_data["treatmentBranches"]:
            treatment_branch = experiment.branches.get(slug=treatment_branch_data["slug"])

            treatment_branch_feature_values_data = treatment_branch_data.pop(
                "featureValues"
            )
            for treatment_branch_feature_value in treatment_branch.feature_values.all():
                self.assertIn(
                    {
                        "featureConfig": {
                            "id": treatment_branch_feature_value.feature_config.id
                        },
                        "enabled": treatment_branch_feature_value.enabled,
                        "value": treatment_branch_feature_value.value,
                    },
                    treatment_branch_feature_values_data,
                )

            self.assertEqual(
                treatment_branch_data,
                {
                    "slug": treatment_branch.slug,
                    "name": treatment_branch.name,
                    "description": treatment_branch.description,
                    "ratio": treatment_branch.ratio,
                    "screenshots": [
                        {"description": s.description, "image": s.image.url}
                        for s in treatment_branch.screenshots.all()
                    ],
                },
            )

    def test_experiments_with_documentation_links_return_link_data(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
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

    def test_experiment_returns_country_and_locale_and_language(self):
        user_email = "user@example.com"
        NimbusExperimentFactory.create(publish_status=NimbusExperiment.PublishStatus.IDLE)

        response = self.query(
            """
            query {
                experiments {
                    countries {
                        code
                        name
                    }
                    locales {
                        code
                        name
                    }
                    languages {
                        code
                        name
                    }
                }
            }
            """,
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        experiment_data = content["data"]["experiments"][0]

        for locale in Locale.objects.all():
            self.assertIn(
                {"code": locale.code, "name": locale.name}, experiment_data["locales"]
            )

        for country in Country.objects.all():
            self.assertIn(
                {"code": country.code, "name": country.name}, experiment_data["countries"]
            )

        for language in Language.objects.all():
            self.assertIn(
                {"code": language.code, "name": language.name},
                experiment_data["languages"],
            )


class TestNimbusExperimentBySlugQuery(GraphQLTestCase):
    GRAPHQL_URL = reverse("nimbus-api-graphql")

    def test_experiment_by_slug_ready_for_review(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[
                NimbusFeatureConfigFactory(
                    application=NimbusExperiment.Application.DESKTOP
                )
            ],
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
                        warnings
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
            experiment_data["readyForReview"],
            {"message": {}, "warnings": {}, "ready": True},
        )

    def test_experiment_by_slug_with_parent(self):
        user_email = "user@example.com"
        parent_experiment = NimbusExperimentFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED, parent=parent_experiment
        )

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    parent {
                        slug
                        name
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
        self.assertEqual(experiment_data["parent"]["slug"], parent_experiment.slug)
        self.assertEqual(experiment_data["parent"]["name"], parent_experiment.name)

    def test_experiment_by_slug_without_parent(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    parent {
                        name
                        slug
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
        self.assertIsNone(experiment_data["parent"])

    def test_experiment_by_slug_not_ready_for_review(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            hypothesis=NimbusExperiment.HYPOTHESIS_DEFAULT,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[
                NimbusFeatureConfigFactory(
                    application=NimbusExperiment.Application.DESKTOP
                )
            ],
        )

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    readyForReview {
                        message
                        warnings
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
                "warnings": {},
                "ready": False,
            },
        )

    def test_experiment_by_slug_not_found(self):
        user_email = "user@example.com"
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )

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
            NimbusExperimentFactory.Lifecycles.CREATED,
            targeting_config_slug=NimbusExperiment.TargetingConfig.TARGETING_FIRST_RUN,
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

    def test_experiment_computed_end_date_proposed(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
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
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
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
            str(experiment.end_date),
        )

    def test_experiment_in_review_can_review(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_REVIEW_REQUESTED
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
            NimbusExperimentFactory.Lifecycles.CREATED,
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
            NimbusExperimentFactory.Lifecycles.LAUNCH_REJECT,
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
            NimbusExperimentFactory.Lifecycles.CREATED,
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
            NimbusExperimentFactory.Lifecycles.LAUNCH_REVIEW_REQUESTED,
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
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,
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
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_TIMEOUT,
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

    def test_recipe_json_returns_serialized_data_for_unpublished_experiment(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
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

    def test_recipe_json_returns_published_dto_for_published_experiment(self):
        user_email = "user@example.com"
        published_dto = {"field": "value"}
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED, published_dto=published_dto
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
            json.dumps(published_dto, indent=2, sort_keys=True),
        )

    def test_paused_experiment_returns_date(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_PAUSED,
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

    @parameterized.expand(
        [
            [NimbusExperimentFactory.Lifecycles.PAUSING_REVIEW_REQUESTED, False, True],
            [NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE, False, True],
            [NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_WAITING, False, True],
            [NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_TIMEOUT, False, True],
            [NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_APPROVE, True, False],
            [NimbusExperimentFactory.Lifecycles.PAUSING_REJECT, False, False],
            [NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_REJECT, False, False],
        ]
    )
    def test_experiment_pause_pending(self, lifecycle, expected_paused, expected_pending):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(lifecycle)
        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    isEnrollmentPaused
                    isEnrollmentPausePending
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiment_data = content["data"]["experimentBySlug"]
        self.assertEqual(experiment_data["isEnrollmentPaused"], expected_paused)
        self.assertEqual(experiment_data["isEnrollmentPausePending"], expected_pending)

    def test_signoff_recommendations(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
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

    def test_targeting_config_slug_for_valid_targeting_config_returns_name(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            targeting_config_slug=NimbusExperiment.TargetingConfig.TARGETING_FIRST_RUN,
        )

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    targetingConfigSlug
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
            experiment_data["targetingConfigSlug"],
            NimbusExperiment.TargetingConfig.TARGETING_FIRST_RUN.value,
        )

    def test_targeting_config(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            targeting_config_slug=NimbusExperiment.TargetingConfig.TARGETING_FIRST_RUN,
        )

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    targetingConfig {
                        label
                        value
                        description
                        applicationValues
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
        print(experiment_data)
        self.assertEqual(
            experiment_data["targetingConfig"],
            [
                {
                    "label": NimbusExperiment.TargetingConfig.TARGETING_FIRST_RUN.label,
                    "value": NimbusExperiment.TargetingConfig.TARGETING_FIRST_RUN.value,
                    "applicationValues": list(
                        NimbusExperiment.TARGETING_CONFIGS[
                            NimbusExperiment.TargetingConfig.TARGETING_FIRST_RUN.value
                        ].application_choice_names
                    ),
                    "description": NimbusExperiment.TARGETING_CONFIGS[
                        NimbusExperiment.TargetingConfig.TARGETING_FIRST_RUN.value
                    ].description,
                }
            ],
        )

    def test_targeting_configs_with_empty_targeting_config_slug(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            targeting_config_slug="",
        )

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    targetingConfig {
                        label
                        value
                        description
                        applicationValues
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
        print(experiment_data)
        self.assertEqual(
            experiment_data["targetingConfig"],
            [
                {
                    "label": NimbusExperiment.TargetingConfig.NO_TARGETING.label,
                    "value": NimbusExperiment.TargetingConfig.NO_TARGETING.value,
                    "applicationValues": list(
                        NimbusExperiment.TARGETING_CONFIGS[
                            NimbusExperiment.TargetingConfig.NO_TARGETING.value
                        ].application_choice_names
                    ),
                    "description": NimbusExperiment.TARGETING_CONFIGS[
                        NimbusExperiment.TargetingConfig.NO_TARGETING.value
                    ].description,
                }
            ],
        )

    def test_targeting_config_slug_for_deprecated_targeting_config_returns_slug(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            targeting_config_slug="deprecated_targeting",
        )

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    targetingConfigSlug
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
            experiment_data["targetingConfigSlug"],
            "deprecated_targeting",
        )

    def test_feature_config_with_single_feature(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    application=NimbusExperiment.Application.DESKTOP
                )
            ],
        )

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    featureConfig {
                        id
                        application
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
        feature_config = experiment.feature_configs.get()
        self.assertEqual(
            experiment_data["featureConfig"],
            {"id": feature_config.id, "application": "DESKTOP"},
        )

    def test_feature_config_with_multiple_features(self):
        user_email = "user@example.com"
        feature_config1 = NimbusFeatureConfigFactory.create(
            slug="a", application=NimbusExperiment.Application.DESKTOP
        )
        feature_config2 = NimbusFeatureConfigFactory.create(
            slug="b", application=NimbusExperiment.Application.DESKTOP
        )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config1, feature_config2],
        )

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    featureConfig {
                        id
                        application
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
            experiment_data["featureConfig"],
            {"id": feature_config1.id, "application": "DESKTOP"},
        )

    def test_branches(self):
        user_email = "user@example.com"
        feature_config1 = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            slug="a",
        )
        feature_config2 = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            slug="b",
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config1, feature_config2],
        )

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    referenceBranch {
                        id
                        name
                        slug
                        description
                        ratio
                        featureEnabled
                        featureValue
                    }
                    treatmentBranches {
                        id
                        name
                        slug
                        description
                        ratio
                        featureEnabled
                        featureValue
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
            experiment_data["referenceBranch"],
            {
                "id": experiment.reference_branch.id,
                "name": experiment.reference_branch.name,
                "slug": experiment.reference_branch.slug,
                "ratio": experiment.reference_branch.ratio,
                "description": experiment.reference_branch.description,
                "featureEnabled": (
                    experiment.reference_branch.feature_values.get(
                        feature_config=feature_config1
                    ).enabled
                ),
                "featureValue": experiment.reference_branch.feature_values.get(
                    feature_config=feature_config1
                ).value,
            },
        )

        for treatment_branch in experiment.treatment_branches:
            self.assertIn(
                {
                    "id": treatment_branch.id,
                    "name": treatment_branch.name,
                    "slug": treatment_branch.slug,
                    "ratio": treatment_branch.ratio,
                    "description": treatment_branch.description,
                    "featureEnabled": treatment_branch.feature_values.get(
                        feature_config=feature_config1
                    ).enabled,
                    "featureValue": treatment_branch.feature_values.get(
                        feature_config=feature_config1
                    ).value,
                },
                experiment_data["treatmentBranches"],
            )


class TestNimbusConfigQuery(GraphQLTestCase):
    GRAPHQL_URL = reverse("nimbus-api-graphql")

    def test_nimbus_config(self):
        user_email = "user@example.com"
        feature_configs = NimbusFeatureConfigFactory.create_batch(10)
        experiment = NimbusExperimentFactory.create()

        response = self.query(
            """
            query{
                nimbusConfig{
                    applications {
                        label
                        value
                    }
                    channels {
                        label
                        value
                    }
                    conclusionRecommendations {
                        label
                        value
                    }
                    applicationConfigs {
                        application
                        channels {
                            label
                            value
                        }
                    }
                    firefoxVersions {
                        label
                        value
                    }
                    allFeatureConfigs {
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
                    owners {
                        username
                    }
                    targetingConfigs {
                        label
                        value
                        description
                        applicationValues
                    }
                    documentationLink {
                        label
                        value
                    }
                    hypothesisDefault
                    maxPrimaryOutcomes
                    locales {
                        code
                        name
                    }
                    countries {
                        code
                        name
                    }
                    languages {
                        code
                        name
                    }
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

        assertChoices(config["applications"], NimbusExperiment.Application)
        assertChoices(config["channels"], NimbusExperiment.Channel)
        assertChoices(
            config["conclusionRecommendations"], NimbusExperiment.ConclusionRecommendation
        )
        assertChoices(config["firefoxVersions"], NimbusExperiment.Version)
        assertChoices(config["documentationLink"], NimbusExperiment.DocumentationLink)
        self.assertEqual(len(config["allFeatureConfigs"]), 18)

        for application_config_data in config["applicationConfigs"]:
            application_config = NimbusExperiment.APPLICATION_CONFIGS[
                NimbusExperiment.Application[application_config_data["application"]]
            ]
            channels = [
                channel["value"] for channel in application_config_data["channels"]
            ]
            self.assertEqual(
                set(channels),
                set(
                    [channel.name for channel in application_config.channel_app_id.keys()]
                ),
            )

        self.assertEqual(config["owners"], [{"username": experiment.owner.username}])

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
            self.assertIn(
                {
                    "id": feature_config.id,
                    "name": feature_config.name,
                    "slug": feature_config.slug,
                    "description": feature_config.description,
                },
                config["allFeatureConfigs"],
            )

        for choice in NimbusExperiment.TargetingConfig:
            self.assertIn(
                {
                    "label": choice.label,
                    "value": choice.value,
                    "description": NimbusExperiment.TARGETING_CONFIGS[
                        choice.value
                    ].description,
                    "applicationValues": list(
                        NimbusExperiment.TARGETING_CONFIGS[
                            choice.value
                        ].application_choice_names
                    ),
                },
                config["targetingConfigs"],
            )

        self.assertEqual(config["hypothesisDefault"], NimbusExperiment.HYPOTHESIS_DEFAULT)
        self.assertEqual(
            config["maxPrimaryOutcomes"], NimbusExperiment.MAX_PRIMARY_OUTCOMES
        )

        for locale in Locale.objects.all():
            self.assertIn({"code": locale.code, "name": locale.name}, config["locales"])

        for country in Country.objects.all():
            self.assertIn(
                {"code": country.code, "name": country.name}, config["countries"]
            )

        for language in Language.objects.all():
            self.assertIn(
                {"code": language.code, "name": language.name}, config["languages"]
            )
