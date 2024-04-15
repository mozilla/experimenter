import datetime
from decimal import Decimal
from unittest import mock

from django.test import TestCase
from django.utils.text import slugify
from parameterized import parameterized

from experimenter.base.tests.factories import (
    CountryFactory,
    LanguageFactory,
    LocaleFactory,
)
from experimenter.experiments.api.v5.serializers import NimbusExperimentSerializer
from experimenter.experiments.changelog_utils import generate_nimbus_changelog
from experimenter.experiments.models import (
    NimbusBucketRange,
    NimbusExperiment,
    NimbusExperimentBranchThroughExcluded,
    NimbusExperimentBranchThroughRequired,
)
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
    NimbusVersionedSchemaFactory,
)
from experimenter.openidc.tests.factories import UserFactory
from experimenter.outcomes import Outcomes
from experimenter.outcomes.tests import mock_valid_outcomes
from experimenter.projects.tests.factories import ProjectFactory
from experimenter.targeting.constants import TargetingConstants


@mock_valid_outcomes
class TestNimbusExperimentSerializer(TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Outcomes.clear_cache()

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

        mock_preview_task_patcher = mock.patch(
            "experimenter.experiments.api.v5.serializers."
            "nimbus_synchronize_preview_experiments_in_kinto"
        )
        self.mock_preview_task = mock_preview_task_patcher.start()
        self.addCleanup(mock_preview_task_patcher.stop)

        mock_push_task_patcher = mock.patch(
            "experimenter.experiments.api.v5.serializers."
            "nimbus_check_kinto_push_queue_by_collection"
        )
        self.mock_push_task = mock_push_task_patcher.start()
        self.addCleanup(mock_push_task_patcher.stop)

    def test_serializer_creates_experiment_and_sets_slug_and_owner(self):
        data = {
            "name": "Test 1234",
            "hypothesis": "Test hypothesis",
            "application": NimbusExperiment.Application.DESKTOP,
            "risk_mitigation_link": "https://example.com/risk",
            "public_description": "Test description",
            "changelog_message": "test changelog message",
        }

        serializer = NimbusExperimentSerializer(data=data, context={"user": self.user})
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()

        self.assertEqual(experiment.slug, slugify(data["name"]))
        self.assertEqual(experiment.name, data["name"])
        self.assertEqual(experiment.application, data["application"])
        self.assertEqual(experiment.hypothesis, data["hypothesis"])
        self.assertEqual(experiment.risk_mitigation_link, data["risk_mitigation_link"])
        self.assertEqual(experiment.public_description, data["public_description"])
        # Owner should match the email of the user who created the experiment
        self.assertEqual(experiment.owner, self.user)
        self.assertFalse(experiment.branches.exists())

    @parameterized.expand(list(NimbusExperiment.Application))
    def test_serializer_sets_channel_to_application_channel(self, application):
        data = {
            "name": "Test 1234",
            "hypothesis": "Test hypothesis",
            "application": application,
            "risk_mitigation_link": "https://example.com/risk",
            "public_description": "Test description",
            "changelog_message": "test changelog message",
        }

        serializer = NimbusExperimentSerializer(data=data, context={"user": self.user})
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()

        self.assertIn(experiment.channel, experiment.application_config.channel_app_id)

    def test_serializer_accepts_blank_risk_mitigation_link(self):
        data = {
            "name": "Test 1234",
            "hypothesis": "Test hypothesis",
            "application": NimbusExperiment.Application.DESKTOP,
            "public_description": "Test description",
            "risk_mitigation_link": "",
            "changelog_message": "test changelog message",
        }
        serializer = NimbusExperimentSerializer(data=data, context={"user": self.user})
        self.assertTrue(serializer.is_valid())

    def test_serializer_rejects_long_name(self):
        data = {
            "name": "a" * 81,
            "hypothesis": "Test hypothesis",
            "application": NimbusExperiment.Application.DESKTOP,
            "public_description": "Test description",
            "changelog_message": "test changelog message",
        }

        serializer = NimbusExperimentSerializer(data=data, context={"user": self.user})
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_required_fields_for_creating_experiment(self):
        data = {
            "name": "",
            "hypothesis": NimbusExperiment.HYPOTHESIS_DEFAULT,
            "application": "",
            "changelog_message": "test changelog message",
        }

        serializer = NimbusExperimentSerializer(
            data=data,
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)
        self.assertIn("hypothesis", serializer.errors)
        self.assertIn("application", serializer.errors)

    def test_allows_empty_values_for_all_fields_existing_experiment(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            subscribers=[],
        )
        data = {
            "name": "",
            "hypothesis": "",
            "public_description": "",
            "feature_configs": [],
            "treatment_branches": [],
            "primary_outcomes": [],
            "secondary_outcomes": [],
            "channel": NimbusExperiment.Channel.NO_CHANNEL,
            "firefox_min_version": NimbusExperiment.Version.NO_VERSION,
            "population_percent": "0.0",
            "proposed_duration": 0,
            "proposed_enrollment": 0,
            "proposed_release_date": None,
            "targeting_config_slug": NimbusExperiment.TargetingConfig.NO_TARGETING,
            "total_enrolled_clients": 0,
            "changelog_message": "test changelog message",
            "countries": [],
            "locales": [],
            "languages": [],
            "projects": [],
            "subscribers": [],
        }

        serializer = NimbusExperimentSerializer(
            experiment,
            data,
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        serializer.save()
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.name, "")
        self.assertEqual(experiment.hypothesis, "")
        self.assertEqual(experiment.public_description, "")
        self.assertFalse(experiment.feature_configs.exists())
        self.assertEqual(experiment.treatment_branches, [])
        self.assertEqual(experiment.primary_outcomes, [])
        self.assertEqual(experiment.secondary_outcomes, [])
        self.assertEqual(experiment.channel, NimbusExperiment.Channel.NO_CHANNEL)
        self.assertEqual(
            experiment.firefox_min_version, NimbusExperiment.Version.NO_VERSION
        )
        self.assertEqual(experiment.population_percent, 0.0)
        self.assertEqual(experiment.proposed_duration, 0)
        self.assertEqual(experiment.proposed_enrollment, 0)
        self.assertEqual(experiment.proposed_release_date, None)
        self.assertEqual(
            experiment.targeting_config_slug,
            NimbusExperiment.TargetingConfig.NO_TARGETING,
        )
        self.assertEqual(experiment.total_enrolled_clients, 0)
        self.assertEqual(list(experiment.countries.all()), [])
        self.assertEqual(list(experiment.locales.all()), [])
        self.assertEqual(list(experiment.languages.all()), [])
        self.assertEqual(list(experiment.projects.all()), [])
        self.assertEqual(list(experiment.subscribers.all()), [])

    def test_serializer_rejects_bad_name(self):
        data = {
            "name": "&^%&^%&^%&^%^&%^&",
            "hypothesis": "Test hypothesis",
            "application": NimbusExperiment.Application.DESKTOP,
            "public_description": "Test description",
            "changelog_message": "test changelog message",
        }

        serializer = NimbusExperimentSerializer(data=data, context={"user": self.user})
        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "Name needs to contain alphanumeric characters", serializer.errors["name"]
        )

    def test_serializer_returns_error_for_non_unique_slug(self):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            name="non unique slug",
            slug="non-unique-slug",
        )

        data = {
            "name": "non-unique slug",
            "hypothesis": "Test hypothesis",
            "application": NimbusExperiment.Application.DESKTOP,
            "public_description": "Test description",
            "changelog_message": "test changelog message",
        }

        serializer = NimbusExperimentSerializer(data=data, context={"user": self.user})
        self.assertFalse(serializer.is_valid())

        self.assertIn(
            "Name maps to a pre-existing slug, please choose another name",
            serializer.errors["name"],
        )

    def test_serializer_rejects_default_hypothesis(self):
        data = {
            "name": "Test 1234",
            "hypothesis": NimbusExperiment.HYPOTHESIS_DEFAULT,
            "application": NimbusExperiment.Application.DESKTOP,
            "public_description": "Test description",
            "changelog_message": "test changelog message",
        }

        serializer = NimbusExperimentSerializer(data=data, context={"user": self.user})
        self.assertFalse(serializer.is_valid())
        self.assertIn("hypothesis", serializer.errors)

    def test_saves_new_experiment_with_changelog(self):
        data = {
            "application": NimbusExperiment.Application.DESKTOP,
            "hypothesis": "It does the thing",
            "name": "The Thing",
            "public_description": "Does it do the thing?",
            "changelog_message": "test changelog message",
        }

        serializer = NimbusExperimentSerializer(data=data, context={"user": self.user})

        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()
        self.assertEqual(experiment.changes.count(), 1)
        self.assertEqual(experiment.application, NimbusExperiment.Application.DESKTOP)
        self.assertEqual(experiment.hypothesis, "It does the thing")
        self.assertEqual(experiment.name, "The Thing")
        self.assertEqual(experiment.slug, "the-thing")

    def test_saves_existing_experiment_with_changelog(self):
        feature_config = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            schemas=[
                NimbusVersionedSchemaFactory.build(
                    version=None,
                    set_pref_vars={"baz": "foo.bar.baz"},
                ),
            ],
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.FENIX,
            hypothesis="Existing hypothesis",
            name="Existing Name",
            slug="existing-name",
            public_description="Existing public description",
        )
        self.assertEqual(experiment.changes.count(), 1)

        data = {
            "application": NimbusExperiment.Application.DESKTOP,
            "hypothesis": "New Hypothesis",
            "name": "New Name",
            "public_description": "New public description",
            "changelog_message": "test changelog message",
            "feature_configs": [feature_config.id],
            "prevent_pref_conflicts": True,
        }

        serializer = NimbusExperimentSerializer(
            experiment, data=data, context={"user": self.user}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        experiment = serializer.save()
        self.assertEqual(experiment.changes.count(), 2)
        self.assertEqual(experiment.application, NimbusExperiment.Application.DESKTOP)
        self.assertEqual(experiment.hypothesis, "New Hypothesis")
        self.assertEqual(experiment.name, "New Name")
        self.assertEqual(experiment.slug, "existing-name")
        self.assertEqual(experiment.public_description, "New public description")
        self.assertEqual(list(experiment.feature_configs.all()), [feature_config])
        self.assertEqual(experiment.prevent_pref_conflicts, True)

    def test_saves_branches_single_feature(self):
        feature_config = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[],
        )
        experiment.branches.all().delete()

        data = {
            "feature_configs": [feature_config.id],
            "reference_branch": {
                "name": "control",
                "description": "a control",
                "ratio": 1,
                "feature_values": [
                    {
                        "feature_config": feature_config.id,
                        "value": "",
                    },
                ],
            },
            "treatment_branches": [
                {
                    "name": "treatment",
                    "description": "a treatment",
                    "ratio": 1,
                    "feature_values": [
                        {
                            "feature_config": feature_config.id,
                            "value": "{'this': 'that'}",
                        }
                    ],
                },
            ],
            "changelog_message": "test changelog message",
        }

        serializer = NimbusExperimentSerializer(
            experiment, data=data, context={"user": self.user}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        experiment = serializer.save()
        self.assertEqual(list(experiment.feature_configs.all()), [feature_config])
        self.assertEqual(experiment.reference_branch.name, "control")
        self.assertEqual(experiment.reference_branch.description, "a control")
        self.assertEqual(experiment.reference_branch.ratio, 1)

        reference_feature_value = experiment.reference_branch.feature_values.get()
        self.assertEqual(reference_feature_value.feature_config, feature_config)
        self.assertEqual(reference_feature_value.value, "")

        treatment_branch = experiment.treatment_branches[0]
        self.assertEqual(treatment_branch.name, "treatment")
        self.assertEqual(treatment_branch.description, "a treatment")
        self.assertEqual(treatment_branch.ratio, 1)

        treatment_feature_value = treatment_branch.feature_values.get()
        self.assertEqual(treatment_feature_value.feature_config, feature_config)
        self.assertEqual(treatment_feature_value.value, "{'this': 'that'}")

    def test_saves_branches_multi_feature(self):
        feature1 = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP
        )
        feature2 = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[],
        )
        experiment.branches.all().delete()

        data = {
            "feature_configs": [feature1.id, feature2.id],
            "reference_branch": {
                "name": "control",
                "description": "a control",
                "ratio": 1,
                "feature_values": [
                    {
                        "feature_config": feature1.id,
                        "value": "",
                    },
                    {
                        "feature_config": feature2.id,
                        "value": "",
                    },
                ],
            },
            "treatment_branches": [
                {
                    "name": "treatment",
                    "description": "a treatment",
                    "ratio": 1,
                    "feature_values": [
                        {
                            "feature_config": feature1.id,
                            "value": f"{{'{feature1.name}': 'value'}}",
                        },
                        {
                            "feature_config": feature2.id,
                            "value": f"{{'{feature2.name}': 'value'}}",
                        },
                    ],
                }
            ],
            "changelog_message": "test changelog message",
        }

        serializer = NimbusExperimentSerializer(
            experiment, data=data, context={"user": self.user}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        experiment = serializer.save()
        self.assertEqual(set(experiment.feature_configs.all()), {feature1, feature2})
        self.assertEqual(experiment.reference_branch.name, "control")
        self.assertEqual(experiment.reference_branch.description, "a control")
        self.assertEqual(experiment.reference_branch.ratio, 1)

        for feature in [feature1, feature2]:
            reference_feature_value = experiment.reference_branch.feature_values.get(
                feature_config=feature
            )
            self.assertEqual(reference_feature_value.value, "")

        treatment_branch = experiment.treatment_branches[0]
        self.assertEqual(treatment_branch.name, "treatment")
        self.assertEqual(treatment_branch.description, "a treatment")
        self.assertEqual(treatment_branch.ratio, 1)

        for feature in [feature1, feature2]:
            treatment_feature_value = treatment_branch.feature_values.get(
                feature_config=feature
            )
            self.assertEqual(
                treatment_feature_value.value, f"{{'{feature.name}': 'value'}}"
            )

    def test_serializer_updates_audience_on_experiment(self):
        country = CountryFactory.create()
        locale = LocaleFactory.create()
        language = LanguageFactory.create()
        project = ProjectFactory.create()

        experiment = NimbusExperimentFactory(
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            population_percent=0.0,
            proposed_duration=0,
            proposed_enrollment=0,
            proposed_release_date=None,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            total_enrolled_clients=0,
            is_sticky=False,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            {
                "channel": NimbusExperiment.Channel.BETA,
                "firefox_min_version": NimbusExperiment.Version.FIREFOX_83,
                "population_percent": 10,
                "proposed_duration": 120,
                "proposed_enrollment": 42,
                "proposed_release_date": "2023-12-12",
                "targeting_config_slug": (TargetingConstants.TargetingConfig.FIRST_RUN),
                "total_enrolled_clients": 100,
                "changelog_message": "test changelog message",
                "countries": [country.id],
                "locales": [locale.id],
                "languages": [language.id],
                "projects": [project.id],
                "is_sticky": True,
            },
            context={"user": self.user},
        )
        self.assertEqual(experiment.changes.count(), 0)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        experiment = serializer.save()
        self.assertEqual(experiment.changes.count(), 1)
        self.assertEqual(experiment.channel, NimbusExperiment.Channel.BETA)
        self.assertEqual(
            experiment.firefox_min_version, NimbusExperiment.Version.FIREFOX_83
        )
        self.assertEqual(experiment.population_percent, 10)
        self.assertEqual(experiment.proposed_duration, 120)
        self.assertEqual(experiment.proposed_enrollment, 42)
        self.assertEqual(experiment.proposed_release_date, datetime.date(2023, 12, 12))
        self.assertEqual(
            experiment.targeting_config_slug,
            TargetingConstants.TargetingConfig.FIRST_RUN,
        )
        self.assertEqual(experiment.total_enrolled_clients, 100)
        self.assertEqual(list(experiment.countries.all()), [country])
        self.assertEqual(list(experiment.locales.all()), [locale])
        self.assertEqual(list(experiment.languages.all()), [language])
        self.assertEqual(list(experiment.projects.all()), [project])
        self.assertTrue(experiment.is_sticky)

    @parameterized.expand(
        [
            [False, None],
            [False, -1.0],
            [False, 0.00001],
            [True, 0.0],
            [True, 1.0],
            [True, 99.9999],
            [True, 100.0],
            [False, 101.0],
        ]
    )
    def test_population_percent_bounds_check(self, expected_valid, population_percent):
        experiment = NimbusExperimentFactory()
        serializer = NimbusExperimentSerializer(
            experiment,
            {
                "population_percent": population_percent,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertEqual(serializer.is_valid(), expected_valid)
        if not expected_valid:
            self.assertIn("population_percent", serializer.errors)
        else:
            self.assertNotIn("population_percent", serializer.errors)

    @parameterized.expand(
        [
            [NimbusExperiment.Status.DRAFT, NimbusExperiment.Status.PREVIEW],
            [NimbusExperiment.Status.PREVIEW, NimbusExperiment.Status.DRAFT],
        ]
    )
    def test_valid_status_update(self, from_status, to_status):
        experiment = NimbusExperimentFactory(status=from_status)
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status": to_status,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertEqual(experiment.changes.count(), 0)
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()
        self.assertEqual(experiment.changes.count(), 1)
        self.assertEqual(experiment.status, to_status)

    def test_status_with_invalid_target_status(self):
        experiment = NimbusExperimentFactory(status=NimbusExperiment.Status.DRAFT)
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status": NimbusExperiment.Status.COMPLETE,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertEqual(experiment.changes.count(), 0)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "status": [
                    "Nimbus Experiment status cannot transition from Draft to Complete."
                ]
            },
            serializer.errors,
        )

    def test_status_with_invalid_target_status_next(self):
        experiment = NimbusExperimentFactory(status=NimbusExperiment.Status.DRAFT)
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": NimbusExperiment.PublishStatus.REVIEW,
                "status_next": NimbusExperiment.Status.COMPLETE,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertEqual(experiment.changes.count(), 0)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "status_next": [
                    "Invalid choice for status_next: 'Complete' - with status 'Draft',"
                    " the only valid choices are 'None, Live'"
                ]
            },
            serializer.errors,
        )

    def test_status_restrictions(self):
        experiment = NimbusExperimentFactory(status=NimbusExperiment.Status.LIVE)
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "name": "new name",
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertEqual(experiment.changes.count(), 0)
        self.assertFalse(serializer.is_valid())
        self.assertIn("experiment", serializer.errors)

    def test_preview_status_generates_bucket_allocation(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED, population_percent=Decimal("50.0")
        )

        self.assertFalse(NimbusBucketRange.objects.filter(experiment=experiment).exists())

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status": NimbusExperiment.Status.PREVIEW,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()

        self.assertTrue(NimbusBucketRange.objects.filter(experiment=experiment).exists())
        self.assertEqual(experiment.bucket_range.count, 5000)

    def test_publish_status_approved_generates_bucket_allocation(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            population_percent=Decimal("50.0"),
        )

        experiment.publish_status = NimbusExperiment.PublishStatus.REVIEW
        experiment.save()
        generate_nimbus_changelog(experiment, experiment.owner, "test message")

        self.assertFalse(NimbusBucketRange.objects.filter(experiment=experiment).exists())

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": NimbusExperiment.PublishStatus.APPROVED,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()

        self.assertTrue(NimbusBucketRange.objects.filter(experiment=experiment).exists())
        self.assertEqual(experiment.bucket_range.count, 5000)

    def test_end_enrollment_does_not_change_bucket_allocation(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_REVIEW_REQUESTED,
            is_rollout=True,
            population_percent=Decimal("50.0"),
        )
        bucket_id = experiment.bucket_range.id

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": NimbusExperiment.PublishStatus.REVIEW,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()

        self.assertTrue(NimbusBucketRange.objects.filter(experiment=experiment).exists())
        self.assertEqual(experiment.bucket_range.count, 5000)
        self.assertEqual(experiment.bucket_range.id, bucket_id)

    def test_end_experiment_does_not_change_bucket_allocation(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_REVIEW_REQUESTED,
            is_rollout=True,
            population_percent=Decimal("50.0"),
        )
        bucket_id = experiment.bucket_range.id

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": NimbusExperiment.PublishStatus.REVIEW,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()

        self.assertTrue(NimbusBucketRange.objects.filter(experiment=experiment).exists())
        self.assertEqual(experiment.bucket_range.count, 5000)
        self.assertEqual(experiment.bucket_range.id, bucket_id)

    def test_live_rollout_allocates_buckets(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE,
            is_rollout=True,
            population_percent=Decimal("50.0"),
        )

        bucket_id = experiment.bucket_range.id

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": NimbusExperiment.PublishStatus.APPROVED,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()

        self.assertTrue(NimbusBucketRange.objects.filter(experiment=experiment).exists())
        self.assertEqual(experiment.bucket_range.count, 5000)
        self.assertNotEqual(experiment.bucket_range.id, bucket_id)

    def test_live_experiment_does_not_allocate_buckets(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_REVIEW_REQUESTED,
            is_rollout=False,
            population_percent=Decimal("50.0"),
        )

        bucket_id = experiment.bucket_range.id

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": NimbusExperiment.PublishStatus.APPROVED,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()

        self.assertEqual(experiment.bucket_range.id, bucket_id)

    @parameterized.expand(
        [
            [NimbusExperimentFactory.Lifecycles.CREATED, NimbusExperiment.Status.PREVIEW],
            [NimbusExperimentFactory.Lifecycles.PREVIEW, NimbusExperiment.Status.DRAFT],
        ]
    )
    def test_preview_draft_transition_invokes_kinto_task(
        self, start_lifecycle, to_status
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            start_lifecycle, population_percent=Decimal("50.0")
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status": to_status,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()
        self.assertEqual(experiment.status, to_status)
        self.mock_preview_task.apply_async.assert_called_with(countdown=5)

    def test_set_status_already_draft_doesnt_invoke_kinto_task(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED, population_percent=Decimal("50.0")
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status": NimbusExperiment.Status.DRAFT,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.DRAFT)
        self.mock_preview_task.apply_async.assert_not_called()

    @parameterized.expand(
        [
            [True, NimbusExperiment.PublishStatus.IDLE],
            [False, NimbusExperiment.PublishStatus.IDLE],
            [True, NimbusExperiment.PublishStatus.REVIEW],
            [False, NimbusExperiment.PublishStatus.REVIEW],
        ]
    )
    def test_update_publish_status_doesnt_invoke_push_task(
        self,
        is_rollout,
        publish_status,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_rollout=is_rollout,
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": publish_status,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()
        self.assertEqual(experiment.publish_status, publish_status)
        self.mock_preview_task.apply_async.assert_not_called()

    @parameterized.expand(
        [
            [True, True, NimbusExperiment.PublishStatus.IDLE],
            [True, True, NimbusExperiment.PublishStatus.REVIEW],
            [True, False, NimbusExperiment.PublishStatus.IDLE],
            [True, False, NimbusExperiment.PublishStatus.REVIEW],
            [False, True, NimbusExperiment.PublishStatus.IDLE],
            [False, True, NimbusExperiment.PublishStatus.REVIEW],
            [False, False, NimbusExperiment.PublishStatus.IDLE],
            [False, False, NimbusExperiment.PublishStatus.REVIEW],
        ]
    )
    def test_update_is_dirty_doesnt_invoke_push_task(
        self,
        is_rollout,
        is_dirty,
        publish_status,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            is_rollout=is_rollout,
            population_percent=50,
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": publish_status,
                "is_rollout_dirty": is_dirty,
                "population_percent": 50.0,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()
        self.assertEqual(experiment.publish_status, publish_status)
        self.assertEqual(experiment.is_rollout_dirty, is_dirty)
        self.mock_preview_task.apply_async.assert_not_called()

    @parameterized.expand(
        [
            [True, True],
            [True, False],
            [False, True],
            [False, False],
        ]
    )
    def test_draft_is_dirty_flag_doesnt_invoke_push_task(
        self,
        is_rollout,
        is_rollout_dirty,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_rollout=is_rollout,
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "is_rollout_dirty": is_rollout_dirty,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()
        self.assertEqual(experiment.is_rollout_dirty, is_rollout_dirty)
        self.mock_preview_task.apply_async.assert_not_called()

    @parameterized.expand(list(NimbusExperiment.Application))
    def test_update_publish_status_to_approved_invokes_push_task(self, application):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_REVIEW_REQUESTED,
            application=application,
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": NimbusExperiment.PublishStatus.APPROVED,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()
        self.assertEqual(
            experiment.publish_status, NimbusExperiment.PublishStatus.APPROVED
        )
        self.mock_push_task.apply_async.assert_called_with(
            countdown=5,
            args=[experiment.application_config.kinto_collection],
        )

    def test_serializer_updates_outcomes_on_experiment(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            primary_outcomes=[],
            secondary_outcomes=[],
        )

        outcomes = [
            o.slug for o in Outcomes.by_application(NimbusExperiment.Application.DESKTOP)
        ]
        primary_outcomes = outcomes[: NimbusExperiment.MAX_PRIMARY_OUTCOMES]
        secondary_outcomes = outcomes[NimbusExperiment.MAX_PRIMARY_OUTCOMES :]

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "primary_outcomes": primary_outcomes,
                "secondary_outcomes": secondary_outcomes,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

        experiment = serializer.save()
        self.assertEqual(experiment.primary_outcomes, primary_outcomes)
        self.assertEqual(experiment.secondary_outcomes, secondary_outcomes)

    def test_serializer_rejects_invalid_outcome_slugs(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            primary_outcomes=[],
            secondary_outcomes=[],
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "primary_outcomes": ["invalid-slug"],
                "secondary_outcomes": ["invalid-slug"],
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("primary_outcomes", serializer.errors)
        self.assertIn("secondary_outcomes", serializer.errors)

    def test_serializer_rejects_outcomes_for_wrong_application(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.FENIX,
            primary_outcomes=[],
            secondary_outcomes=[],
        )

        outcomes = [
            o.slug for o in Outcomes.by_application(NimbusExperiment.Application.DESKTOP)
        ]
        primary_outcomes = outcomes[: NimbusExperiment.MAX_PRIMARY_OUTCOMES]
        secondary_outcomes = outcomes[NimbusExperiment.MAX_PRIMARY_OUTCOMES :]

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "primary_outcomes": primary_outcomes,
                "secondary_outcomes": secondary_outcomes,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("primary_outcomes", serializer.errors)
        self.assertIn("secondary_outcomes", serializer.errors)

    def test_serializer_rejects_duplicate_outcomes(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            primary_outcomes=[],
            secondary_outcomes=[],
        )

        outcomes = [
            o.slug
            for o in Outcomes.by_application(NimbusExperiment.Application.DESKTOP)[
                : NimbusExperiment.MAX_PRIMARY_OUTCOMES
            ]
        ]

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "primary_outcomes": outcomes,
                "secondary_outcomes": outcomes,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("primary_outcomes", serializer.errors)

    def test_serializer_rejects_too_many_primary_outcomes(self):
        NimbusExperiment.MAX_PRIMARY_OUTCOMES = 1

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            primary_outcomes=[],
            secondary_outcomes=[],
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "primary_outcomes": [
                    "someoutcome",
                    "someotheroutcome",
                    "toomanyoutcomes",
                ],
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("primary_outcomes", serializer.errors)

    def test_can_request_review_from_preview(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PREVIEW,
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status": NimbusExperiment.Status.DRAFT,
                "publish_status": NimbusExperiment.PublishStatus.REVIEW,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        experiment = serializer.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.REVIEW)

    def test_rollout_can_request_review_from_live_idle_to_live_review(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            is_rollout=True,
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status": NimbusExperiment.Status.LIVE,
                "publish_status": NimbusExperiment.PublishStatus.REVIEW,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        experiment = serializer.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.REVIEW)

    def test_rollout_can_request_review_from_live_dirty(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_DIRTY,
            is_rollout=True,
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status": NimbusExperiment.Status.LIVE,
                "publish_status": NimbusExperiment.PublishStatus.REVIEW,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        experiment = serializer.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.LIVE)
        self.assertTrue(experiment.is_rollout_dirty)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.REVIEW)

    def test_allow_live_rollout_to_be_dirty(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle=NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            is_rollout=True,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status": NimbusExperiment.Status.LIVE,
                "publish_status": NimbusExperiment.PublishStatus.IDLE,
                "status_next": NimbusExperiment.Status.LIVE,
                "is_rollout_dirty": True,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

    def test_can_review_for_non_requesting_user(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_REVIEW_REQUESTED,
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": NimbusExperiment.PublishStatus.APPROVED,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        experiment = serializer.save()
        self.assertEqual(
            experiment.publish_status, NimbusExperiment.PublishStatus.APPROVED
        )

    def test_cant_review_for_requesting_user(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )

        experiment.publish_status = NimbusExperiment.PublishStatus.REVIEW
        experiment.save()

        generate_nimbus_changelog(experiment, experiment.owner, "test message")

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": NimbusExperiment.PublishStatus.APPROVED,
                "changelog_message": "test changelog message",
            },
            context={"user": experiment.owner},
        )

        self.assertFalse(serializer.is_valid(), serializer.errors)
        self.assertIn("publish_status", serializer.errors)

    def test_cant_review_for_requesting_user_dirty(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_DIRTY,
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": NimbusExperiment.PublishStatus.APPROVED,
                "changelog_message": "test changelog message",
            },
            context={"user": experiment.owner},
        )

        self.assertFalse(serializer.is_valid(), serializer.errors)
        self.assertIn("publish_status", serializer.errors)

    @parameterized.expand([[True], [False]])
    def test_can_review_for_requesting_user_when_idle(self, is_rollout):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_rollout=is_rollout,
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": NimbusExperiment.PublishStatus.REVIEW,
                "changelog_message": "test changelog message",
            },
            context={"user": experiment.owner},
        )

        self.assertTrue(serializer.is_valid())

    @parameterized.expand([[True], [False]])
    def test_can_review_for_requesting_user_when_dirty(self, is_rollout):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_DIRTY,
            is_rollout=is_rollout,
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": NimbusExperiment.PublishStatus.REVIEW,
                "changelog_message": "test changelog message",
            },
            context={"user": experiment.owner},
        )

        self.assertTrue(serializer.is_valid())

    def test_can_update_publish_status_for_non_approved_state(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )

        experiment.publish_status = NimbusExperiment.PublishStatus.REVIEW
        experiment.save()

        generate_nimbus_changelog(experiment, experiment.owner, "test message")

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": NimbusExperiment.PublishStatus.IDLE,
                "changelog_message": "test changelog message",
            },
            context={"user": experiment.owner},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        experiment = serializer.save()
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)

    def test_update_population_percent_for_live_rollout(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            is_rollout=True,
            population_percent=50,
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "population_percent": 77,
                "changelog_message": "test changelog message",
            },
            context={"user": experiment.owner},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        experiment = serializer.save()
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)
        self.assertTrue(experiment.is_rollout_dirty)

    def test_no_change_to_population_percent_doesnt_update_live_rollout(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            is_rollout=True,
            population_percent=50,
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "population_percent": 50,
                "changelog_message": "test changelog message",
            },
            context={"user": experiment.owner},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        experiment = serializer.save()
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)
        self.assertFalse(experiment.is_rollout_dirty)

    def test_targeting_config_for_correct_application(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        data = {
            "targeting_config_slug": (NimbusExperiment.TargetingConfig.FIRST_RUN_WIN1903),
            "changelog_message": "updating targeting config",
        }
        serializer = NimbusExperimentSerializer(
            experiment,
            data,
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

    def test_targeting_config_for_wrong_application(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.IOS,
        )
        data = {
            "targeting_config_slug": (NimbusExperiment.TargetingConfig.FIRST_RUN_WIN1903),
            "changelog_message": "updating targeting config",
        }
        serializer = NimbusExperimentSerializer(
            experiment,
            data,
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["targeting_config_slug"],
            [
                "Targeting config 'First start-up users on Windows 10 1903 "
                "(build 18362) or newer' is not available for application "
                "'Firefox for iOS'",
            ],
        )

    def test_enrollment_must_be_less_or_equal_experiment_duration(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )
        data = {
            "proposed_duration": 3,
            "proposed_enrollment": 4,
            "changelog_message": "updating durations",
        }
        serializer = NimbusExperimentSerializer(
            experiment,
            data,
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["proposed_enrollment"],
            [
                "The enrollment duration must be less than or "
                "equal to the experiment duration."
            ],
        )

    @parameterized.expand(
        [
            (True, NimbusExperimentFactory.Lifecycles.CREATED),
            (False, NimbusExperimentFactory.Lifecycles.PREVIEW),
            (False, NimbusExperimentFactory.Lifecycles.LAUNCH_REVIEW_REQUESTED),
            (False, NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE),
            (False, NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING),
            (False, NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE),
            (True, NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE),
        ]
    )
    def test_can_update_is_archived(self, can_update, lifecycle):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
            is_archived=False,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            {"is_archived": True, "changelog_message": "archiving"},
            context={"user": self.user},
        )
        self.assertEqual(serializer.is_valid(), can_update, serializer.errors)
        if can_update:
            experiment = serializer.save()
            self.assertTrue(experiment.is_archived, serializer.errors)
        else:
            self.assertIn("is_archived", serializer.errors, serializer.errors)

    def test_cant_update_other_fields_while_archived(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_archived=True,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            {"name": "New Name", "changelog_message": "updating name"},
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_can_update_qa_status_while_archived(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_archived=True,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            {
                "qa_status": NimbusExperiment.QAStatus.GREEN,
                "changelog_message": "updating name",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())
        self.assertTrue(experiment.is_archived, serializer.errors)

    def test_can_unarchive_experiment(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_archived=True,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            {"is_archived": False, "changelog_message": "unarchiving"},
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        experiment = serializer.save()
        self.assertFalse(experiment.is_archived)

    def test_can_set_proposed_release_date(self):
        release_date = datetime.date.today()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_first_run=True,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            {
                "proposed_release_date": release_date,
                "changelog_message": "Test changelog",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()
        self.assertEqual(experiment.proposed_release_date, release_date)

    def test_can_set_empty_proposed_release_date(self):
        release_date = datetime.date.today()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_first_run=True,
            proposed_release_date=release_date,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            {
                "proposed_release_date": None,
                "changelog_message": "Test changelog",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()
        self.assertIsNone(experiment.proposed_release_date)

    def test_preview_to_draft_sets_published_dto_to_None(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PREVIEW, published_dto="{}"
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            {
                "status": NimbusExperiment.Status.DRAFT,
                "changelog_message": "Test changelog",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        experiment = serializer.save()
        self.assertIsNone(experiment.published_dto)
        self.assertEqual(experiment.proposed_release_date, None)

    def test_can_set_excluded_required_experiments_all_branches(self):
        excluded = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        required = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            {
                "excluded_experiments_branches": [
                    {"excluded_experiment": excluded.id, "branch_slug": None}
                ],
                "required_experiments_branches": [
                    {"required_experiment": required.id, "branch_slug": None}
                ],
                "changelog_message": "Test changelog",
            },
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        experiment = serializer.save()

        self.assertEqual(experiment.excluded_experiments.get(), excluded)
        self.assertTrue(
            NimbusExperimentBranchThroughExcluded.objects.filter(
                parent_experiment=experiment, child_experiment=excluded, branch_slug=None
            ).exists()
        )
        self.assertEqual(experiment.required_experiments.get(), required)
        self.assertTrue(
            NimbusExperimentBranchThroughRequired.objects.filter(
                parent_experiment=experiment, child_experiment=required, branch_slug=None
            ).exists()
        )

    def test_can_set_excluded_required_experiments_specific_branches(self):
        excluded = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        required = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            {
                "excluded_experiments_branches": [
                    {
                        "excluded_experiment": excluded.id,
                        "branch_slug": excluded.reference_branch.slug,
                    }
                ],
                "required_experiments_branches": [
                    {
                        "required_experiment": required.id,
                        "branch_slug": required.reference_branch.slug,
                    }
                ],
                "changelog_message": "Test changelog",
            },
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        experiment = serializer.save()

        self.assertEqual(experiment.excluded_experiments.get(), excluded)
        self.assertTrue(
            NimbusExperimentBranchThroughExcluded.objects.filter(
                parent_experiment=experiment,
                child_experiment=excluded,
                branch_slug=excluded.reference_branch.slug,
            ).exists()
        )
        self.assertEqual(experiment.required_experiments.get(), required)
        self.assertTrue(
            NimbusExperimentBranchThroughRequired.objects.filter(
                parent_experiment=experiment,
                child_experiment=required,
                branch_slug=required.reference_branch.slug,
            ).exists()
        )

    def test_cant_set_excluded_required_experiments_invalid_experiments(self):
        excluded = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        required = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            {
                "excluded_experiments_branches": [
                    {
                        "excluded_experiment": -1,
                        "branch_slug": excluded.reference_branch.slug,
                    }
                ],
                "required_experiments_branches": [
                    {
                        "required_experiment": -2,
                        "branch_slug": required.reference_branch.slug,
                    }
                ],
                "changelog_message": "Test changelog",
            },
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "excluded_experiment",
            [k for e in serializer.errors["excluded_experiments_branches"] for k in e],
        )
        self.assertIn(
            "required_experiment",
            [k for e in serializer.errors["required_experiments_branches"] for k in e],
        )

    def test_cant_set_excluded_required_experiments_invalid_branches(self):
        excluded = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        required = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            {
                "excluded_experiments_branches": [
                    {
                        "excluded_experiment": excluded.id,
                        "branch_slug": "invalid-excluded-branch",
                    }
                ],
                "required_experiments_branches": [
                    {
                        "required_experiment": required.id,
                        "branch_slug": "invalid-required-branch",
                    }
                ],
                "changelog_message": "Test changelog",
            },
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "branch_slug",
            [k for e in serializer.errors["excluded_experiments_branches"] for k in e],
        )
        self.assertIn(
            "branch_slug",
            [k for e in serializer.errors["excluded_experiments_branches"] for k in e],
        )

    def test_can_set_qa_status_and_comment(self):
        non_graded_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        new_status = NimbusExperiment.QAStatus.RED
        serializer = NimbusExperimentSerializer(
            non_graded_experiment,
            {
                "qa_status": new_status,
                "changelog_message": "Test changelog",
            },
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        experiment = serializer.save()
        self.assertEqual(experiment.qa_status, new_status)

        qa_comment = "This is the best experiment ever"
        comment_serializer = NimbusExperimentSerializer(
            non_graded_experiment,
            {
                "qa_comment": qa_comment,
                "changelog_message": "Test changelog",
            },
            context={"user": self.user},
        )

        self.assertTrue(comment_serializer.is_valid(), comment_serializer.errors)
        experiment = comment_serializer.save()
        self.assertEqual(experiment.qa_comment, qa_comment)
