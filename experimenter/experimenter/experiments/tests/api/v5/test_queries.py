import datetime
import json

from django.conf import settings
from django.urls import reverse
from graphene_django.utils.testing import GraphQLTestCase
from parameterized import parameterized

from experimenter.base.models import Country, Language, Locale
from experimenter.base.tests.factories import (
    CountryFactory,
    LanguageFactory,
    LocaleFactory,
)
from experimenter.experiments.api.v5.serializers import (
    NimbusReviewSerializer,
    TransitionConstants,
)
from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusBranchFeatureValue, NimbusExperiment
from experimenter.experiments.tests.factories import (
    NimbusBranchFactory,
    NimbusDocumentationLinkFactory,
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
    NimbusVersionedSchemaFactory,
)
from experimenter.jetstream.tests.mixins import MockSizingDataMixin
from experimenter.openidc.tests.factories import UserFactory
from experimenter.outcomes import Outcomes
from experimenter.projects.models import Project
from experimenter.projects.tests.factories import ProjectFactory


def camelize(snake_str):
    first, *others = snake_str.split("_")
    return "".join([first.lower(), *map(str.title, others)])


class TestNimbusExperimentsQuery(GraphQLTestCase):
    GRAPHQL_URL = reverse("nimbus-api-graphql")
    maxDiff = None

    @parameterized.expand(
        [(lifecycle,) for lifecycle in NimbusExperimentFactory.Lifecycles]
    )
    def test_get_all_experiments_return_experiments_data(self, lifecycle):
        user_email = "user@example.com"
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        project = ProjectFactory.create()
        subscriber = UserFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
            feature_configs=[feature_config],
            projects=[project],
            subscribers=[subscriber],
        )

        response = self.query(
            """
            query getAllExperiments {
                experiments {
                    isArchived
                    isRollout
                    name
                    owner {
                        username
                    }
                    featureConfigs {
                        id
                        slug
                        name
                        description
                        application
                        ownerEmail
                        schema
                    }
                    targetingConfig {
                        label
                        value
                        description
                        applicationValues
                        stickyRequired
                        isFirstRunRequired
                    }
                    slug
                    application
                    firefoxMinVersion
                    firefoxMaxVersion
                    startDate
                    isRolloutDirty
                    isEnrollmentPausePending
                    isEnrollmentPaused
                    proposedDuration
                    proposedEnrollment
                    proposedReleaseDate
                    computedEndDate
                    computedEnrollmentEndDate
                    status
                    statusNext
                    publishStatus
                    qaStatus
                    monitoringDashboardUrl
                    rolloutMonitoringDashboardUrl
                    resultsExpectedDate
                    resultsReady
                    showResultsUrl
                    channel
                    populationPercent
                    projects {
                        id
                        name
                    }
                    hypothesis
                    subscribers {
                        email
                    }
                }
            }
            """,
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiments = content["data"]["experiments"]
        self.assertEqual(len(experiments), 1)
        experiment_data = experiments[0]
        self.assertEqual(
            experiment_data,
            {
                "application": NimbusExperiment.Application(experiment.application).name,
                "channel": NimbusExperiment.Channel(experiment.channel).name,
                "computedEndDate": (
                    str(experiment.computed_end_date)
                    if experiment.computed_end_date is not None
                    else None
                ),
                "computedEnrollmentEndDate": (
                    str(experiment.computed_enrollment_end_date)
                    if experiment.computed_enrollment_end_date is not None
                    else None
                ),
                "featureConfigs": [
                    {
                        "application": NimbusExperiment.Application(
                            feature_config.application
                        ).name,
                        "description": feature_config.description,
                        "id": feature_config.id,
                        "name": feature_config.name,
                        "ownerEmail": feature_config.owner_email,
                        "schema": feature_config.schemas.get(version=None).schema,
                        "slug": feature_config.slug,
                    }
                ],
                "firefoxMaxVersion": NimbusExperiment.Version(
                    experiment.firefox_max_version
                ).name,
                "firefoxMinVersion": NimbusExperiment.Version(
                    experiment.firefox_min_version
                ).name,
                "isArchived": experiment.is_archived,
                "isRolloutDirty": experiment.is_rollout_dirty,
                "isEnrollmentPausePending": experiment.is_enrollment_pause_pending,
                "isEnrollmentPaused": experiment.is_paused_published,
                "isRollout": experiment.is_rollout,
                "monitoringDashboardUrl": experiment.monitoring_dashboard_url,
                "name": experiment.name,
                "owner": {"username": experiment.owner.username},
                "populationPercent": str(experiment.population_percent),
                "proposedDuration": experiment.proposed_duration,
                "proposedEnrollment": experiment.proposed_enrollment,
                "proposedReleaseDate": experiment.proposed_release_date,
                "publishStatus": NimbusExperiment.PublishStatus(
                    experiment.publish_status
                ).name,
                "qaStatus": NimbusExperiment.QAStatus(experiment.qa_status).name,
                "resultsExpectedDate": (
                    str(experiment.results_expected_date)
                    if experiment.results_expected_date is not None
                    else None
                ),
                "resultsReady": experiment.results_ready,
                "rolloutMonitoringDashboardUrl": (
                    experiment.rollout_monitoring_dashboard_url
                ),
                "showResultsUrl": experiment.show_results_url,
                "slug": experiment.slug,
                "startDate": (
                    str(experiment.start_date)
                    if experiment.start_date is not None
                    else None
                ),
                "status": NimbusExperiment.Status(experiment.status).name,
                "statusNext": (
                    NimbusExperiment.Status(experiment.status_next).name
                    if experiment.status_next is not None
                    else None
                ),
                "subscribers": [{"email": str(subscriber.email)}],
                "targetingConfig": [
                    {
                        "applicationValues": list(
                            experiment.targeting_config.application_choice_names
                        ),
                        "description": experiment.targeting_config.description,
                        "isFirstRunRequired": (
                            experiment.targeting_config.is_first_run_required
                        ),
                        "label": experiment.targeting_config.name,
                        "stickyRequired": experiment.targeting_config.sticky_required,
                        "value": experiment.targeting_config.slug,
                    }
                ],
                "projects": [{"id": str(project.id), "name": project.name}],
                "hypothesis": experiment.hypothesis,
            },
        )
        self.assertEqual(experiment_data["hypothesis"], experiment.hypothesis)

    def test_experiments_with_no_branches_returns_empty_reference_treatment_values(
        self,
    ):
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
        self.assertEqual(response.status_code, 200, response.content)
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
        self.assertTrue(len(documentation_links) > 0)

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
        self.assertEqual(response.status_code, 200, response.content)
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
        self.assertEqual(response.status_code, 200, response.content)
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
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiment_data = content["data"]["experiments"][0]

        for locale in Locale.objects.all():
            self.assertIn(
                {"code": locale.code, "name": locale.name}, experiment_data["locales"]
            )

        for country in Country.objects.all():
            self.assertIn(
                {"code": country.code, "name": country.name},
                experiment_data["countries"],
            )

        for language in Language.objects.all():
            self.assertIn(
                {"code": language.code, "name": language.name},
                experiment_data["languages"],
            )

    def test_experiment_returns_project(self):
        user_email = "user@example.com"
        NimbusExperimentFactory.create(publish_status=NimbusExperiment.PublishStatus.IDLE)

        response = self.query(
            """
            query {
                experiments {

                    projects {
                        slug
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

        for project in Project.objects.all():
            self.assertIn(
                {"slug": project.slug, "name": project.name},
                experiment_data["projects"],
            )

    def test_experiment_returns_subscribers(self):
        subscriber = UserFactory.create()
        NimbusExperimentFactory.create(subscribers=[subscriber])

        response = self.query(
            """
            query {
                experiments {
                    subscribers {
                        email
                    }
                }
            }
            """,
            headers={settings.OPENIDC_EMAIL_HEADER: "user@example.com"},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        experiment_data = content["data"]["experiments"][0]

        self.assertIn(
            {"email": subscriber.email},
            experiment_data["subscribers"],
        )


class TestNimbusExperimentBySlugQuery(GraphQLTestCase):
    maxDiff = None
    GRAPHQL_URL = reverse("nimbus-api-graphql")

    @parameterized.expand(
        [(lifecycle,) for lifecycle in NimbusExperimentFactory.Lifecycles]
    )
    def test_get_experiment_by_slug_returns_experiment_data(self, lifecycle):
        user = UserFactory.create()
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        documentation_link = NimbusDocumentationLinkFactory.create()
        country = CountryFactory.create()
        locale = LocaleFactory.create()
        language = LanguageFactory.create()
        project = ProjectFactory.create()
        required = NimbusExperimentFactory.create(application=application)
        excluded = NimbusExperimentFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
            parent=NimbusExperimentFactory.create(),
            feature_configs=[feature_config],
            documentation_links=[documentation_link],
            countries=[country],
            locales=[locale],
            languages=[language],
            projects=[project],
            required_experiments_branches=[required],
            excluded_experiments_branches=[excluded],
        )

        review_request_change = experiment.changes.latest_review_request()
        rejection_change = experiment.changes.latest_rejection()
        timeout_change = experiment.changes.latest_timeout()
        reference_branch = experiment.reference_branch
        reference_feature_value = reference_branch.feature_values.get()
        treatment_branch = experiment.treatment_branches[0]
        treatment_feature_value = treatment_branch.feature_values.get()

        review_serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment).data,
        )
        review_ready = review_serializer.is_valid()

        response = self.query(
            """
            query getExperiment($slug: String!) {
                experimentBySlug(slug: $slug) {
                    id
                    isRollout
                    isArchived
                    canEdit
                    canArchive
                    name
                    slug
                    status
                    statusNext
                    publishStatus
                    monitoringDashboardUrl
                    rolloutMonitoringDashboardUrl
                    resultsReady

                    hypothesis
                    application
                    publicDescription

                    conclusionRecommendation
                    takeawaysGainAmount
                    takeawaysMetricGain
                    takeawaysQbrLearning
                    takeawaysSummary

                    owner {
                        email
                    }

                    parent {
                        name
                        slug
                    }

                    warnFeatureSchema

                    referenceBranch {
                        id
                        name
                        slug
                        description
                        ratio
                        featureValues {
                            featureConfig {
                                id
                            }
                            value
                        }
                        screenshots {
                            id
                            description
                            image
                        }
                    }

                    treatmentBranches {
                        id
                        name
                        slug
                        description
                        ratio
                        featureValues {
                            featureConfig {
                                id
                            }
                            value
                        }
                        screenshots {
                            id
                            description
                            image
                        }
                    }

                    preventPrefConflicts

                    featureConfigs {
                        id
                        slug
                        name
                        description
                        application
                        ownerEmail
                        schema
                        setsPrefs
                    }

                    primaryOutcomes
                    secondaryOutcomes

                    channel
                    firefoxMinVersion
                    firefoxMaxVersion
                    targetingConfigSlug
                    targetingConfig {
                        label
                        value
                        applicationValues
                        description
                        stickyRequired
                        isFirstRunRequired
                    }
                    isSticky
                    isFirstRun
                    jexlTargetingExpression

                    populationPercent
                    totalEnrolledClients
                    proposedEnrollment
                    proposedDuration
                    proposedReleaseDate

                    readyForReview {
                        ready
                        message
                        warnings
                    }

                    startDate
                    computedDurationDays
                    computedEndDate
                    computedEnrollmentDays
                    computedEnrollmentEndDate

                    riskMitigationLink
                    riskRevenue
                    riskBrand
                    riskPartnerRelated

                    signoffRecommendations {
                        qaSignoff
                        vpSignoff
                        legalSignoff
                    }

                    documentationLinks {
                        title
                        link
                    }

                    isRolloutDirty
                    isEnrollmentPausePending
                    isEnrollmentPaused
                    enrollmentEndDate

                    canReview
                    reviewRequest {
                        changedOn
                        changedBy {
                            email
                        }
                    }
                    rejection {
                        message
                        oldStatus
                        oldStatusNext
                        changedOn
                        changedBy {
                            email
                        }
                    }
                    timeout {
                        changedOn
                        changedBy {
                            email
                        }
                    }
                    recipeJson
                    reviewUrl

                    locales {
                        id
                        name
                    }
                    countries {
                        id
                        name
                    }
                    languages {
                        id
                        name
                    }
                    projects {
                        id
                        name
                    }

                    isLocalized
                    localizations
                    isWeb
                    qaStatus

                    requiredExperimentsBranches {
                        requiredExperiment {
                            id
                            slug
                        }
                        branchSlug
                    }
                    excludedExperimentsBranches {
                        excludedExperiment {
                            id
                            slug
                        }
                        branchSlug
                    }
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user.email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiment_data = content["data"]["experimentBySlug"]

        self.assertEqual(
            experiment_data,
            {
                "application": NimbusExperiment.Application(experiment.application).name,
                "canArchive": experiment.can_archive,
                "canEdit": experiment.can_edit,
                "canReview": experiment.can_review(user),
                "channel": NimbusExperiment.Channel(experiment.channel).name,
                "computedDurationDays": experiment.computed_duration_days,
                "computedEndDate": (
                    str(experiment.computed_end_date)
                    if experiment.computed_end_date
                    else None
                ),
                "computedEnrollmentDays": experiment.computed_enrollment_days,
                "computedEnrollmentEndDate": (
                    str(experiment.computed_enrollment_end_date)
                    if experiment.computed_enrollment_end_date
                    else None
                ),
                "conclusionRecommendation": experiment.conclusion_recommendation,
                "countries": [{"id": str(country.id), "name": country.name}],
                "documentationLinks": [
                    {
                        "link": documentation_link.link,
                        "title": NimbusExperiment.DocumentationLink(
                            documentation_link.title
                        ).name,
                    },
                ],
                "enrollmentEndDate": (
                    str(experiment.proposed_enrollment_end_date)
                    if experiment.proposed_enrollment_end_date
                    else None
                ),
                "excludedExperimentsBranches": [
                    {
                        "excludedExperiment": {
                            "id": excluded.id,
                            "slug": excluded.slug,
                        },
                        "branchSlug": excluded.reference_branch.slug,
                    }
                ],
                "featureConfigs": [
                    {
                        "application": NimbusExperiment.Application(
                            feature_config.application
                        ).name,
                        "description": feature_config.description,
                        "id": feature_config.id,
                        "name": feature_config.name,
                        "ownerEmail": feature_config.owner_email,
                        "schema": feature_config.schemas.get(version=None).schema,
                        "setsPrefs": bool(
                            feature_config.schemas.get(version=None).sets_prefs
                        ),
                        "slug": feature_config.slug,
                    }
                ],
                "firefoxMaxVersion": NimbusExperiment.Version(
                    experiment.firefox_max_version
                ).name,
                "firefoxMinVersion": NimbusExperiment.Version(
                    experiment.firefox_min_version
                ).name,
                "hypothesis": experiment.hypothesis,
                "id": experiment.id,
                "isArchived": experiment.is_archived,
                "isRolloutDirty": experiment.is_rollout_dirty,
                "isEnrollmentPausePending": experiment.is_enrollment_pause_pending,
                "isEnrollmentPaused": experiment.is_paused_published,
                "isFirstRun": experiment.is_first_run,
                "isLocalized": experiment.is_localized,
                "isRollout": experiment.is_rollout,
                "isSticky": experiment.is_sticky,
                "isWeb": NimbusExperiment.APPLICATION_CONFIGS[
                    experiment.application
                ].is_web,
                "jexlTargetingExpression": experiment.targeting,
                "languages": [{"id": str(language.id), "name": language.name}],
                "locales": [{"id": str(locale.id), "name": locale.name}],
                "localizations": experiment.localizations,
                "monitoringDashboardUrl": experiment.monitoring_dashboard_url,
                "name": experiment.name,
                "owner": {"email": experiment.owner.email},
                "parent": {
                    "slug": experiment.parent.slug,
                    "name": experiment.parent.name,
                },
                "populationPercent": str(experiment.population_percent),
                "preventPrefConflicts": experiment.prevent_pref_conflicts,
                "primaryOutcomes": experiment.primary_outcomes,
                "projects": [{"id": str(project.id), "name": project.name}],
                "proposedDuration": experiment.proposed_duration,
                "proposedEnrollment": experiment.proposed_enrollment,
                "proposedReleaseDate": experiment.proposed_release_date,
                "publicDescription": experiment.public_description,
                "publishStatus": NimbusExperiment.PublishStatus(
                    experiment.publish_status
                ).name,
                "qaStatus": NimbusExperiment.QAStatus(experiment.qa_status).name,
                "readyForReview": {
                    "message": review_serializer.errors,
                    "ready": review_ready,
                    "warnings": review_serializer.warnings,
                },
                "recipeJson": json.dumps(
                    experiment.published_dto
                    or NimbusExperimentSerializer(experiment).data,
                    indent=2,
                    sort_keys=True,
                ),
                "referenceBranch": {
                    "description": reference_branch.description,
                    "featureValues": [
                        {
                            "featureConfig": {
                                "id": reference_feature_value.feature_config.id,
                            },
                            "value": reference_feature_value.value,
                        }
                    ],
                    "id": reference_branch.id,
                    "name": reference_branch.name,
                    "ratio": reference_branch.ratio,
                    "screenshots": [
                        {
                            "description": screenshot.description,
                            "id": screenshot.id,
                            "image": screenshot.image.url,
                        }
                        for screenshot in reference_branch.screenshots.all()
                    ],
                    "slug": reference_branch.slug,
                },
                "rejection": (
                    {
                        "changedBy": {"email": rejection_change.changed_by.email},
                        "changedOn": rejection_change.changed_on.isoformat(),
                        "message": rejection_change.message,
                        "oldStatus": NimbusExperiment.Status(
                            rejection_change.old_status
                        ).name,
                        "oldStatusNext": NimbusExperiment.Status(
                            rejection_change.old_status_next
                        ).name,
                    }
                    if rejection_change
                    else None
                ),
                "requiredExperimentsBranches": [
                    {
                        "requiredExperiment": {
                            "id": required.id,
                            "slug": required.slug,
                        },
                        "branchSlug": required.reference_branch.slug,
                    }
                ],
                "resultsReady": experiment.results_ready,
                "reviewRequest": (
                    {
                        "changedBy": {"email": review_request_change.changed_by.email},
                        "changedOn": review_request_change.changed_on.isoformat(),
                    }
                    if review_request_change
                    else None
                ),
                "reviewUrl": experiment.review_url,
                "riskBrand": experiment.risk_brand,
                "riskMitigationLink": experiment.risk_mitigation_link,
                "riskPartnerRelated": experiment.risk_partner_related,
                "riskRevenue": experiment.risk_revenue,
                "rolloutMonitoringDashboardUrl": (
                    experiment.rollout_monitoring_dashboard_url
                ),
                "secondaryOutcomes": experiment.secondary_outcomes,
                "signoffRecommendations": {
                    camelize(k): v for k, v in experiment.signoff_recommendations.items()
                },
                "slug": experiment.slug,
                "startDate": (
                    str(experiment.start_date) if experiment.start_date else None
                ),
                "status": NimbusExperiment.Status(experiment.status).name,
                "statusNext": (
                    NimbusExperiment.Status(experiment.status_next).name
                    if experiment.status_next is not None
                    else None
                ),
                "takeawaysGainAmount": experiment.takeaways_gain_amount,
                "takeawaysMetricGain": experiment.takeaways_metric_gain,
                "takeawaysQbrLearning": experiment.takeaways_qbr_learning,
                "takeawaysSummary": experiment.takeaways_summary,
                "targetingConfig": [
                    {
                        "applicationValues": list(
                            experiment.targeting_config.application_choice_names
                        ),
                        "description": experiment.targeting_config.description,
                        "isFirstRunRequired": (
                            experiment.targeting_config.is_first_run_required
                        ),
                        "label": experiment.targeting_config.name,
                        "stickyRequired": experiment.targeting_config.sticky_required,
                        "value": experiment.targeting_config.slug,
                    }
                ],
                "targetingConfigSlug": experiment.targeting_config_slug,
                "timeout": (
                    {
                        "changedBy": {"email": timeout_change.changed_by.email},
                        "changedOn": timeout_change.changed_on.isoformat(),
                    }
                    if timeout_change
                    else None
                ),
                "totalEnrolledClients": experiment.total_enrolled_clients,
                "treatmentBranches": [
                    {
                        "description": treatment_branch.description,
                        "featureValues": [
                            {
                                "featureConfig": {
                                    "id": treatment_feature_value.feature_config.id,
                                },
                                "value": treatment_feature_value.value,
                            }
                        ],
                        "id": treatment_branch.id,
                        "name": treatment_branch.name,
                        "ratio": treatment_branch.ratio,
                        "screenshots": [
                            {
                                "description": screenshot.description,
                                "id": screenshot.id,
                                "image": screenshot.image.url,
                            }
                            for screenshot in treatment_branch.screenshots.all()
                        ],
                        "slug": treatment_branch.slug,
                    }
                ],
                "warnFeatureSchema": False,
            },
        )

    def test_experiment_by_slug_ready_for_review(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            feature_configs=[
                NimbusFeatureConfigFactory(
                    application=NimbusExperiment.Application.DESKTOP
                )
            ],
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
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
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiment = content["data"]["experimentBySlug"]
        self.assertIsNone(experiment)

    def test_experiment_jexl_targeting_expression(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            targeting_config_slug=NimbusExperiment.TargetingConfig.FIRST_RUN,
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
        assert experiment.proposed_end_date
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
            experiment_data["reviewRequest"]["changedBy"]["email"],
            experiment.owner.email,
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
        self.assertEqual(response.status_code, 200, response.content)
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
        self.assertEqual(response.status_code, 200, response.content)
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
        self.assertEqual(response.status_code, 200, response.content)
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
        self.assertEqual(response.status_code, 200, response.content)
        experiment_data = content["data"]["experimentBySlug"]
        self.assertEqual(
            experiment_data["recipeJson"],
            json.dumps(published_dto, indent=2, sort_keys=True),
        )

    def test_paused_experiment_returns_date(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_PAUSED,
            start_date=datetime.date(2021, 1, 1),
            proposed_enrollment=7,
        )

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
            targeting_config_slug=NimbusExperiment.TargetingConfig.FIRST_RUN,
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
            NimbusExperiment.TargetingConfig.FIRST_RUN.value,
        )

    def test_targeting_config(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            targeting_config_slug=NimbusExperiment.TargetingConfig.FIRST_RUN,
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
                        stickyRequired
                        isFirstRunRequired
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
            experiment_data["targetingConfig"],
            [
                {
                    "label": NimbusExperiment.TARGETING_CONFIGS[
                        NimbusExperiment.TargetingConfig.FIRST_RUN.value
                    ].name,
                    "value": NimbusExperiment.TargetingConfig.FIRST_RUN.value,
                    "applicationValues": list(
                        NimbusExperiment.TARGETING_CONFIGS[
                            NimbusExperiment.TargetingConfig.FIRST_RUN.value
                        ].application_choice_names
                    ),
                    "description": NimbusExperiment.TARGETING_CONFIGS[
                        NimbusExperiment.TargetingConfig.FIRST_RUN.value
                    ].description,
                    "stickyRequired": NimbusExperiment.TARGETING_CONFIGS[
                        NimbusExperiment.TargetingConfig.FIRST_RUN.value
                    ].sticky_required,
                    "isFirstRunRequired": NimbusExperiment.TARGETING_CONFIGS[
                        NimbusExperiment.TargetingConfig.FIRST_RUN.value
                    ].is_first_run_required,
                }
            ],
        )

    def test_targeting_config_returns_empty_if_slug_not_found(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            targeting_config_slug="test_slug_does_not_exist",
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
                        stickyRequired
                        isFirstRunRequired
                    }
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
            experiment_data["targetingConfig"],
            [],
        )
        self.assertEqual(
            experiment_data["targetingConfigSlug"],
            "test_slug_does_not_exist",
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
                    featureConfigs {
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
            experiment_data["featureConfigs"],
            [
                {
                    "id": feature_config.id,
                    "application": NimbusExperiment.Application.DESKTOP.name,
                }
            ],
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
                    featureConfigs {
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
        self.assertEqual(len(experiment_data["featureConfigs"]), 2)
        self.assertIn(
            {
                "id": feature_config1.id,
                "application": NimbusExperiment.Application.DESKTOP.name,
            },
            experiment_data["featureConfigs"],
        )
        self.assertIn(
            {
                "id": feature_config2.id,
                "application": NimbusExperiment.Application.DESKTOP.name,
            },
            experiment_data["featureConfigs"],
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
                        featureValues {
                            featureConfig { id }
                            value
                        }
                    }
                    treatmentBranches {
                        id
                        name
                        slug
                        description
                        ratio
                        featureValues {
                            featureConfig { id }
                            value
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
            experiment_data["referenceBranch"],
            {
                "id": experiment.reference_branch.id,
                "name": experiment.reference_branch.name,
                "slug": experiment.reference_branch.slug,
                "ratio": experiment.reference_branch.ratio,
                "description": experiment.reference_branch.description,
                "featureValues": [
                    {
                        "featureConfig": {"id": feature_config1.id},
                        "value": experiment.reference_branch.feature_values.get(
                            feature_config=feature_config1
                        ).value,
                    },
                    {
                        "featureConfig": {"id": feature_config2.id},
                        "value": experiment.reference_branch.feature_values.get(
                            feature_config=feature_config2
                        ).value,
                    },
                ],
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
                    "featureValues": [
                        {
                            "featureConfig": {"id": feature_config1.id},
                            "value": treatment_branch.feature_values.get(
                                feature_config=feature_config1
                            ).value,
                        },
                        {
                            "featureConfig": {"id": feature_config2.id},
                            "value": treatment_branch.feature_values.get(
                                feature_config=feature_config2
                            ).value,
                        },
                    ],
                },
                experiment_data["treatmentBranches"],
            )

    def test_query_prevent_pref_conflicts(self):
        user_email = "user@example.com"
        feature = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            schemas=[
                NimbusVersionedSchemaFactory.build(
                    version=None,
                    sets_prefs=["foo.bar.baz"],
                ),
            ],
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature],
            prevent_pref_conflicts=True,
        )
        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    preventPrefConflicts
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200, response.content)

        content = json.loads(response.content)
        experiment_data = content["data"]["experimentBySlug"]
        self.assertEqual(experiment_data["preventPrefConflicts"], True)

    def test_query_localizations(self):
        user_email = "user@example.com"
        en_us_locale = LocaleFactory.create(code="en-US")
        en_ca_locale = LocaleFactory.create(code="en-CA")
        fr_locale = LocaleFactory.create(code="fr")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_localized=True,
            locales=[en_us_locale, en_ca_locale, fr_locale],
        )

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    isLocalized
                    localizations
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200, response.content)

        content = json.loads(response.content)
        experiment_data = content["data"]["experimentBySlug"]
        self.assertEqual(experiment_data["isLocalized"], True)

    @parameterized.expand(
        [
            ("invalid json", None),
            (json.dumps({}), {}),
        ]
    )
    def test_query_localizations_recipe_json(self, l10n_json, expected):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_localized=True,
            localizations=l10n_json,
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
            headers={settings.OPENIDC_EMAIL_HEADER: "user@example.com"},
        )

        self.assertEqual(response.status_code, 200, response.content)

        content = json.loads(response.content)
        recipe_json = json.loads(content["data"]["experimentBySlug"]["recipeJson"])

        self.assertEqual(recipe_json["localizations"], expected)

    def test_get_changelogs(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    changes {
                        changedBy {
                            email
                        }
                        changedOn
                        message
                        oldStatusNext
                        oldStatus
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
            experiment_data["changes"],
            [
                {
                    "changedBy": {"email": c.changed_by.email},
                    "changedOn": c.changed_on.isoformat(),
                    "message": c.message,
                    "oldStatusNext": c.old_status_next,
                    "oldStatus": c.old_status,
                }
                for c in experiment.changes.all().order_by("changed_on")
            ],
        )

    def test_query_feature_order(self):
        feature1 = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP
        )
        feature2 = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP
        )
        feature3 = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP
        )

        self.assertTrue(feature1.id < feature2.id < feature3.id)

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature2.id, feature1.id, feature3.id],
        )

        experiment.branches.all().delete()
        experiment.reference_branch = NimbusBranchFactory(
            experiment=experiment, feature_values=[]
        )
        NimbusBranchFeatureValue.objects.bulk_create(
            [
                NimbusBranchFeatureValue(
                    branch=experiment.reference_branch,
                    feature_config=feature3,
                    value="""{"value": 3}""",
                ),
                NimbusBranchFeatureValue(
                    branch=experiment.reference_branch,
                    feature_config=feature2,
                    value="""{"value": 2}""",
                ),
                NimbusBranchFeatureValue(
                    branch=experiment.reference_branch,
                    feature_config=feature1,
                    value="""{"value": 1}""",
                ),
            ]
        )

        treatment = NimbusBranchFactory(
            experiment=experiment,
            feature_values=[],
        )
        NimbusBranchFeatureValue.objects.bulk_create(
            [
                NimbusBranchFeatureValue(
                    branch=treatment,
                    feature_config=feature2,
                    value="""{"value": 2}""",
                ),
                NimbusBranchFeatureValue(
                    branch=treatment,
                    feature_config=feature3,
                    value="""{"value": 3}""",
                ),
                NimbusBranchFeatureValue(
                    branch=treatment,
                    feature_config=feature1,
                    value="""{"value": 1}""",
                ),
            ]
        ),
        experiment.branches.add(treatment)
        experiment.save()

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    referenceBranch {
                        featureValues {
                            featureConfig { id }
                            value
                        }
                    }

                    treatmentBranches {
                        featureValues {
                            featureConfig { id }
                            value
                        }
                    }
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: "user@example.com"},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiment_data = content["data"]["experimentBySlug"]

        self.assertEqual(len(experiment_data["treatmentBranches"]), 1)

        reference_branch = experiment_data["referenceBranch"]
        treatment_branch = experiment_data["treatmentBranches"][0]

        self.assertEqual(
            reference_branch,
            {
                "featureValues": [
                    {
                        "featureConfig": {"id": feature1.id},
                        "value": """{"value": 1}""",
                    },
                    {
                        "featureConfig": {"id": feature2.id},
                        "value": """{"value": 2}""",
                    },
                    {
                        "featureConfig": {"id": feature3.id},
                        "value": """{"value": 3}""",
                    },
                ]
            },
        )

        self.assertEqual(
            treatment_branch,
            {
                "featureValues": [
                    {
                        "featureConfig": {"id": feature1.id},
                        "value": """{"value": 1}""",
                    },
                    {
                        "featureConfig": {"id": feature2.id},
                        "value": """{"value": 2}""",
                    },
                    {
                        "featureConfig": {"id": feature3.id},
                        "value": """{"value": 3}""",
                    },
                ]
            },
        )


class TestNimbusExperimentsByApplicationMetaQuery(GraphQLTestCase):
    GRAPHQL_URL = reverse("nimbus-api-graphql")

    @property
    def default_headers(self):
        return {settings.OPENIDC_EMAIL_HEADER: "user@example.com"}

    def test_query_excludes_other_applications(self):
        experiments_by_application = {
            application.value: NimbusExperimentFactory.create_with_lifecycle(
                NimbusExperimentFactory.Lifecycles.CREATED,
                application=application,
            )
            for application in list(NimbusExperiment.Application)
        }

        for application in list(NimbusExperiment.Application):
            response = self.query(
                """
                query getAllExperimentsByApplication(
                    $application: NimbusExperimentApplicationEnum!
                ) {
                    experimentsByApplication(application: $application) {
                        id
                        name
                        slug
                        publicDescription
                    }
                }
                """,
                variables={
                    "application": application.name,
                },
                headers=self.default_headers,
            )

            self.assertEqual(response.status_code, 200, response.content)
            content = json.loads(response.content)
            experiments = content["data"]["experimentsByApplication"]

            experiment = experiments_by_application[application.value]
            self.assertEqual(len(experiments), 1)
            self.assertIn(
                {
                    "id": experiment.id,
                    "name": experiment.name,
                    "slug": experiment.slug,
                    "publicDescription": experiment.public_description,
                },
                experiments,
            )


class TestNimbusConfigQuery(MockSizingDataMixin, GraphQLTestCase):
    GRAPHQL_URL = reverse("nimbus-api-graphql")

    def test_nimbus_config(self):
        self.setup_cached_sizing_data()
        user_email = "user@example.com"
        feature_configs = NimbusFeatureConfigFactory.create_batch(10)
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        documentation_link = NimbusDocumentationLinkFactory.create()
        country = CountryFactory.create()
        locale = LocaleFactory.create()
        language = LanguageFactory.create()
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            feature_configs=[feature_config],
            documentation_links=[documentation_link],
            countries=[country],
            locales=[locale],
            languages=[language],
        )

        response = self.query(
            """
            query {
                nimbusConfig {
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
                    allFeatureConfigs {
                        id
                        name
                        slug
                        description
                        application
                        ownerEmail
                        schema
                        setsPrefs
                    }
                    firefoxVersions {
                        label
                        value
                    }
                    outcomes {
                        friendlyName
                        slug
                        application
                        description
                        isDefault
                        metrics {
                            slug
                            friendlyName
                            description
                        }
                    }
                    owners {
                        username
                    }
                    targetingConfigs {
                        label
                        value
                        description
                        applicationValues
                        stickyRequired
                        isFirstRunRequired
                    }
                    hypothesisDefault
                    documentationLink {
                        label
                        value
                    }
                    maxPrimaryOutcomes
                    locales {
                        id
                        name
                    }
                    countries {
                        id
                        name
                    }
                    languages {
                        id
                        name
                    }
                    projects {
                        id
                        name
                    }
                    qaStatus {
                        label
                        value
                    }
                    takeaways {
                        label
                        value
                    }
                    types {
                        label
                        value
                    }
                    statusUpdateExemptFields {
                        all
                        experiments
                        rollouts
                    }
                    populationSizingData
                }
            }
            """,
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        config = content["data"]["nimbusConfig"]

        def assertChoices(data, text_choices):
            self.assertEqual(len(data), len(text_choices.names))
            for index, name in enumerate(text_choices.names):
                self.assertEqual(data[index]["label"], text_choices[name].label)
                self.assertEqual(data[index]["value"], name)

        assertChoices(config["applications"], NimbusExperiment.Application)
        assertChoices(config["takeaways"], NimbusExperiment.Takeaways)
        assertChoices(config["qaStatus"], NimbusExperiment.QAStatus)
        assertChoices(config["types"], NimbusExperiment.Type)
        assertChoices(config["channels"], NimbusExperiment.Channel)
        assertChoices(
            config["conclusionRecommendations"],
            NimbusExperiment.ConclusionRecommendation,
        )

        pop_sizing_data = self.get_cached_sizing_data()
        self.assertEqual(
            config["populationSizingData"], pop_sizing_data.json(exclude_unset=True)
        )

        self.assertEqual(
            len(config["firefoxVersions"]), len(NimbusExperiment.Version.names)
        )
        self.assertEqual(
            TransitionConstants.STATUS_UPDATE_EXEMPT_FIELDS,
            config["statusUpdateExemptFields"][0],
        )
        for _index, name in enumerate(NimbusExperiment.Version.names):
            self.assertIn(
                {"label": NimbusExperiment.Version[name].label, "value": name},
                config["firefoxVersions"],
            )

        self.assertEqual(
            {
                "label": NimbusExperiment.Version.NO_VERSION.label,
                "value": "NO_VERSION",
            },
            config["firefoxVersions"][0],
        )

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
                {channel.name for channel in application_config.channel_app_id},
            )

        self.assertEqual(
            {owner["username"] for owner in config["owners"]},
            {experiment.owner.username for experiment in NimbusExperiment.objects.all()},
        )

        for outcome in Outcomes.all():
            self.assertIn(
                {
                    "slug": outcome.slug,
                    "friendlyName": outcome.friendly_name,
                    "application": NimbusExperiment.Application(outcome.application).name,
                    "description": outcome.description,
                    "isDefault": outcome.is_default,
                    "metrics": [
                        {
                            "slug": metric.slug,
                            "friendlyName": metric.friendly_name,
                            "description": metric.description,
                        }
                        for metric in outcome.metrics
                    ],
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
                    "application": NimbusExperiment.Application(
                        feature_config.application
                    ).name,
                    "ownerEmail": feature_config.owner_email,
                    "schema": feature_config.schemas.get(version=None).schema,
                    "setsPrefs": bool(
                        feature_config.schemas.get(version=None).sets_prefs
                    ),
                },
                config["allFeatureConfigs"],
            )

        for targeting_config_choice in NimbusExperiment.TargetingConfig:
            targeting_config = NimbusExperiment.TARGETING_CONFIGS[
                targeting_config_choice.value
            ]
            self.assertIn(
                {
                    "label": targeting_config_choice.label,
                    "value": targeting_config_choice.value,
                    "description": targeting_config.description,
                    "stickyRequired": targeting_config.sticky_required,
                    "applicationValues": list(targeting_config.application_choice_names),
                    "isFirstRunRequired": targeting_config.is_first_run_required,
                },
                config["targetingConfigs"],
            )

        self.assertEqual(config["hypothesisDefault"], NimbusExperiment.HYPOTHESIS_DEFAULT)
        self.assertEqual(
            config["maxPrimaryOutcomes"], NimbusExperiment.MAX_PRIMARY_OUTCOMES
        )

        self.assertTrue(Locale.objects.all().exists())
        for locale in Locale.objects.all():
            self.assertIn({"id": str(locale.id), "name": locale.name}, config["locales"])

        self.assertTrue(Country.objects.all().exists())
        for country in Country.objects.all():
            self.assertIn(
                {"id": str(country.id), "name": country.name}, config["countries"]
            )

        self.assertTrue(Language.objects.all().exists())
        for language in Language.objects.all():
            self.assertIn(
                {"id": str(language.id), "name": language.name}, config["languages"]
            )

        self.assertTrue(Project.objects.all().exists())
        for project in Project.objects.all():
            self.assertIn(
                {"id": str(project.id), "name": project.name}, config["projects"]
            )
