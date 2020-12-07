from django.test import TestCase
from django.utils.text import slugify

from experimenter.experiments.api.v5.serializers import (
    NimbusAudienceUpdateSerializer,
    NimbusBranchSerializer,
    NimbusBranchUpdateSerializer,
    NimbusExperimentOverviewSerializer,
    NimbusProbeSetUpdateSerializer,
    NimbusReadyForReviewSerializer,
    NimbusStatusUpdateSerializer,
)
from experimenter.experiments.constants.nimbus import NimbusConstants
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.models.nimbus import NimbusFeatureConfig
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusProbeSetFactory,
)
from experimenter.experiments.tests.factories.nimbus import NimbusFeatureConfigFactory
from experimenter.openidc.tests.factories import UserFactory

BASIC_JSON_SCHEMA = """\
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "description": "Password autocomplete",
  "type": "object",
  "properties": {
    "directMigrateSingleProfile": {
      "description": "Should we directly migrate a single profile?",
      "type": "boolean"
     }
   },
  "additionalProperties": false
}
"""


class TestCreateNimbusExperimentOverviewSerializer(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_serializer_creates_experiment_and_sets_slug_and_owner(self):
        data = {
            "name": "Test 1234",
            "hypothesis": "Test hypothesis",
            "application": NimbusExperiment.Application.DESKTOP.value,
            "public_description": "Test description",
        }

        serializer = NimbusExperimentOverviewSerializer(
            data=data, context={"user": self.user}
        )
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()

        self.assertEqual(experiment.slug, slugify(data["name"]))
        self.assertEqual(experiment.name, data["name"])
        self.assertEqual(experiment.application, data["application"])
        self.assertEqual(experiment.hypothesis, data["hypothesis"])
        self.assertEqual(experiment.public_description, data["public_description"])
        # Owner should match the email of the user who created the experiment
        self.assertEqual(experiment.owner, self.user)

    def test_serializer_rejects_bad_name(self):
        data = {
            "name": "&^%&^%&^%&^%^&%^&",
            "hypothesis": "Test hypothesis",
            "application": NimbusExperiment.Application.DESKTOP.value,
            "public_description": "Test description",
        }

        serializer = NimbusExperimentOverviewSerializer(
            data=data, context={"user": self.user}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "Name needs to contain alphanumeric characters", serializer.errors["name"]
        )

    def test_serializer_returns_error_for_non_unique_slug(self):
        NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.ACCEPTED,
            name="non unique slug",
            slug="non-unique-slug",
        )

        data = {
            "name": "non-unique slug",
            "hypothesis": "Test hypothesis",
            "application": NimbusExperiment.Application.DESKTOP.value,
            "public_description": "Test description",
        }

        serializer = NimbusExperimentOverviewSerializer(
            data=data, context={"user": self.user}
        )
        self.assertFalse(serializer.is_valid())

        self.assertIn(
            "Name maps to a pre-existing slug, please choose another name",
            serializer.errors["name"],
        )

    def test_serializer_rejects_default_hypothesis(self):
        data = {
            "name": "Test 1234",
            "hypothesis": NimbusExperiment.HYPOTHESIS_DEFAULT,
            "application": NimbusExperiment.Application.DESKTOP.value,
            "public_description": "Test description",
        }

        serializer = NimbusExperimentOverviewSerializer(
            data=data, context={"user": self.user}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("hypothesis", serializer.errors)

    def test_saves_new_experiment_with_changelog(self):
        data = {
            "application": NimbusExperiment.Application.DESKTOP,
            "hypothesis": "It does the thing",
            "name": "The Thing",
            "public_description": "Does it do the thing?",
        }

        serializer = NimbusExperimentOverviewSerializer(
            data=data, context={"user": self.user}
        )

        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()
        self.assertEqual(experiment.changes.count(), 1)
        self.assertEqual(experiment.application, NimbusExperiment.Application.DESKTOP)
        self.assertEqual(experiment.hypothesis, "It does the thing")
        self.assertEqual(experiment.name, "The Thing")
        self.assertEqual(experiment.slug, "the-thing")

    def test_saves_existing_experiment_with_changelog(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
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
        }

        serializer = NimbusExperimentOverviewSerializer(
            experiment, data=data, context={"user": self.user}
        )

        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()
        self.assertEqual(experiment.changes.count(), 2)
        self.assertEqual(experiment.application, NimbusExperiment.Application.DESKTOP)
        self.assertEqual(experiment.hypothesis, "New Hypothesis")
        self.assertEqual(experiment.name, "New Name")
        self.assertEqual(experiment.slug, "existing-name")
        self.assertEqual(experiment.public_description, "New public description")


class TestNimbusBranchSerializer(TestCase):
    def test_branch_validates(self):
        branch_data = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "feature_enabled": True,
            "feature_value": "stuff",
        }
        branch_serializer = NimbusBranchSerializer(data=branch_data)
        self.assertTrue(branch_serializer.is_valid())

    def test_branch_missing_feature_value(self):
        branch_data = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "feature_enabled": True,
        }
        branch_serializer = NimbusBranchSerializer(data=branch_data)
        self.assertFalse(branch_serializer.is_valid())
        self.assertEqual(
            branch_serializer.errors,
            {
                "feature_enabled": [
                    "feature_value must be specified if feature_enabled is True."
                ]
            },
        )

    def test_branch_missing_feature_enabled(self):
        branch_data = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "feature_value": "{}",
        }
        branch_serializer = NimbusBranchSerializer(data=branch_data)
        self.assertFalse(branch_serializer.is_valid())
        self.assertEqual(
            branch_serializer.errors,
            {
                "feature_value": [
                    "feature_enabled must be specificed to include a feature_value."
                ]
            },
        )

    def test_branch_name_cant_slugify(self):
        branch_data = {
            "name": "******",
            "description": "a control",
            "ratio": 1,
        }
        branch_serializer = NimbusBranchSerializer(data=branch_data)
        self.assertFalse(branch_serializer.is_valid())
        self.assertEqual(
            branch_serializer.errors,
            {"name": ["Name needs to contain alphanumeric characters."]},
        )


class TestNimbusBranchUpdateSerializer(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_serializer_update_branches(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
        )

        reference_branch = {"name": "control", "description": "a control", "ratio": 1}
        treatment_branches = [
            {"name": "treatment1", "description": "desc1", "ratio": 1},
            {"name": "testment2", "description": "desc2", "ratio": 1},
        ]

        input = {
            "feature_config": None,
            "reference_branch": reference_branch,
            "treatment_branches": treatment_branches,
        }
        serializer = NimbusBranchUpdateSerializer(
            experiment, data=input, partial=True, context={"user": self.user}
        )
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()
        for key, val in reference_branch.items():
            self.assertEqual(getattr(experiment.reference_branch, key), val)

        experiment_treatment_branches = experiment.branches.exclude(
            id=experiment.reference_branch.id
        ).order_by("id")
        for index, branch in enumerate(treatment_branches):
            for key, val in branch.items():
                self.assertEqual(getattr(experiment_treatment_branches[index], key), val)

    def test_serializer_feature_config_validation(self):
        feature_config = NimbusFeatureConfig(schema=BASIC_JSON_SCHEMA)
        feature_config.save()
        experiment = NimbusExperimentFactory(
            status=NimbusExperiment.Status.DRAFT,
        )
        reference_feature_value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        treatment_feature_value = """\
            {"directMigrateSingleProfile": false}
        """.strip()
        reference_branch = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "feature_enabled": True,
            "feature_value": reference_feature_value,
        }
        treatment_branches = [
            {"name": "treatment1", "description": "desc1", "ratio": 1},
            {
                "name": "testment2",
                "description": "desc2",
                "ratio": 1,
                "feature_enabled": True,
                "feature_value": treatment_feature_value,
            },
        ]

        input = {
            "feature_config": feature_config.id,
            "reference_branch": reference_branch,
            "treatment_branches": treatment_branches,
        }
        serializer = NimbusBranchUpdateSerializer(
            experiment, data=input, partial=True, context={"user": self.user}
        )
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()
        for key, val in reference_branch.items():
            self.assertEqual(getattr(experiment.reference_branch, key), val)

        experiment_treatment_branches = experiment.branches.exclude(
            id=experiment.reference_branch.id
        ).order_by("id")
        for index, branch in enumerate(treatment_branches):
            for key, val in branch.items():
                self.assertEqual(getattr(experiment_treatment_branches[index], key), val)

    def test_serializer_feature_config_validation_reference_value_schema_error(self):
        feature_config = NimbusFeatureConfig(schema=BASIC_JSON_SCHEMA)
        feature_config.save()
        experiment = NimbusExperimentFactory(
            status=NimbusExperiment.Status.DRAFT,
        )
        reference_feature_value = """\
            {"DddirectMigrateSingleProfile": true}
        """.strip()
        treatment_feature_value = """\
            {"directMigrateSingleProfile": false}
        """.strip()
        reference_branch = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "feature_enabled": True,
            "feature_value": reference_feature_value,
        }
        treatment_branches = [
            {"name": "treatment1", "description": "desc1", "ratio": 1},
            {
                "name": "testment2",
                "description": "desc2",
                "ratio": 1,
                "feature_enabled": True,
                "feature_value": treatment_feature_value,
            },
        ]

        input = {
            "feature_config": feature_config.id,
            "reference_branch": reference_branch,
            "treatment_branches": treatment_branches,
        }
        serializer = NimbusBranchUpdateSerializer(
            experiment, data=input, partial=True, context={"user": self.user}
        )
        self.assertFalse(serializer.is_valid())
        self.assert_(
            serializer.errors["reference_branch"][0].startswith(
                "Additional properties are not allowed"
            )
        )
        self.assertEqual(len(serializer.errors), 1)

    def test_serializer_feature_config_validation_bad_json_value(self):
        feature_config = NimbusFeatureConfig(schema=BASIC_JSON_SCHEMA)
        feature_config.save()
        experiment = NimbusExperimentFactory(
            status=NimbusExperiment.Status.DRAFT,
        )
        reference_feature_value = """\
            {"directMigrateSingleProfile: true
        """.strip()
        reference_branch = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "feature_enabled": True,
            "feature_value": reference_feature_value,
        }
        treatment_branches = [
            {"name": "treatment1", "description": "desc1", "ratio": 1},
            {
                "name": "testment2",
                "description": "desc2",
                "ratio": 1,
            },
        ]

        input = {
            "feature_config": feature_config.id,
            "reference_branch": reference_branch,
            "treatment_branches": treatment_branches,
        }
        serializer = NimbusBranchUpdateSerializer(
            experiment, data=input, partial=True, context={"user": self.user}
        )
        self.assertFalse(serializer.is_valid())
        self.assert_(
            serializer.errors["reference_branch"][0].startswith("Unterminated string")
        )
        self.assertEqual(len(serializer.errors), 1)

    def test_serializer_feature_config_validation_missing_feature_config(self):
        experiment = NimbusExperimentFactory(
            status=NimbusExperiment.Status.DRAFT,
            feature_config=None,
        )
        reference_feature_value = """\
            {"directMigrateSingleProfile: true
        """.strip()
        reference_branch = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "feature_enabled": True,
            "feature_value": reference_feature_value,
        }
        treatment_branches = [
            {"name": "treatment1", "description": "desc1", "ratio": 1},
            {
                "name": "testment2",
                "description": "desc2",
                "ratio": 1,
            },
        ]

        input = {
            "reference_branch": reference_branch,
            "treatment_branches": treatment_branches,
        }
        serializer = NimbusBranchUpdateSerializer(
            experiment, data=input, partial=True, context={"user": self.user}
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["feature_config"][0],
            "Feature Config required when a branch has feature enabled.",
        )
        self.assertEqual(len(serializer.errors), 1)

    def test_serializer_feature_config_validation_treatment_value_schema_error(self):
        feature_config = NimbusFeatureConfig(schema=BASIC_JSON_SCHEMA)
        feature_config.save()
        experiment = NimbusExperimentFactory(
            status=NimbusExperiment.Status.DRAFT,
        )
        reference_feature_value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        treatment_feature_value = """\
            {"DDdirectMigrateSingleProfile": false}
        """.strip()
        reference_branch = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "feature_enabled": True,
            "feature_value": reference_feature_value,
        }
        treatment_branches = [
            {"name": "treatment1", "description": "desc1", "ratio": 1},
            {
                "name": "testment2",
                "description": "desc2",
                "ratio": 1,
                "feature_enabled": True,
                "feature_value": treatment_feature_value,
            },
        ]

        input = {
            "feature_config": feature_config.id,
            "reference_branch": reference_branch,
            "treatment_branches": treatment_branches,
        }
        serializer = NimbusBranchUpdateSerializer(
            experiment, data=input, partial=True, context={"user": self.user}
        )
        self.assertFalse(serializer.is_valid())
        self.assert_(
            serializer.errors["treatment_branches"][0].startswith(
                "Additional properties are not allowed"
            )
        )
        self.assertEqual(len(serializer.errors), 1)


class TestNimbusProbeSetUpdateSerializer(TestCase):
    def test_serializer_updates_probe_sets_on_experiment(self):
        user = UserFactory()
        experiment = NimbusExperimentFactory(probe_sets=[])
        primary_probe_sets = [
            NimbusProbeSetFactory().id
            for i in range(NimbusExperiment.MAX_PRIMARY_PROBE_SETS)
        ]
        secondary_probe_sets = [NimbusProbeSetFactory().id for i in range(3)]

        serializer = NimbusProbeSetUpdateSerializer(
            experiment,
            {
                "primary_probe_sets": primary_probe_sets,
                "secondary_probe_sets": secondary_probe_sets,
            },
            context={"user": user},
        )

        self.assertEqual(experiment.changes.count(), 0)
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()
        self.assertEqual(experiment.changes.count(), 1)

        self.assertEqual(
            set(primary_probe_sets) | set(secondary_probe_sets),
            set(experiment.probe_sets.all().values_list("id", flat=True)),
        )
        self.assertEqual(
            set([p.id for p in experiment.primary_probe_sets]),
            set(primary_probe_sets),
        )
        self.assertEqual(
            set([p.id for p in experiment.secondary_probe_sets]),
            set(secondary_probe_sets),
        )

    def test_serializer_rejects_duplicate_probes(self):
        user = UserFactory()
        experiment = NimbusExperimentFactory(probe_sets=[])
        probe_sets = [NimbusProbeSetFactory() for i in range(3)]

        serializer = NimbusProbeSetUpdateSerializer(
            experiment,
            {
                "primary_probe_sets": [
                    p.id for p in probe_sets[: NimbusExperiment.MAX_PRIMARY_PROBE_SETS]
                ],
                "secondary_probe_sets": [p.id for p in probe_sets],
            },
            context={"user": user},
        )

        self.assertEqual(experiment.changes.count(), 0)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(experiment.changes.count(), 0)
        self.assertEqual(
            serializer.errors["primary_probe_sets"][0],
            "Primary probe sets cannot overlap with secondary probe sets.",
        )

    def test_serializer_rejects_too_many_primary_probe_sets(self):
        user = UserFactory()
        experiment = NimbusExperimentFactory(probe_sets=[])
        probe_sets = [NimbusProbeSetFactory() for i in range(3)]

        serializer = NimbusProbeSetUpdateSerializer(
            experiment,
            {
                "primary_probe_sets": [p.id for p in probe_sets],
                "secondary_probe_sets": [],
            },
            context={"user": user},
        )

        self.assertEqual(experiment.changes.count(), 0)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(experiment.changes.count(), 0)
        self.assertIn(
            "Exceeded maximum primary probe set limit of",
            serializer.errors["primary_probe_sets"][0],
        )


class TestNimbusAudienceUpdateSerializer(TestCase):
    def test_serializer_updates_audience_on_experiment(self):
        user = UserFactory()
        experiment = NimbusExperimentFactory(
            channels=[],
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=None,
            population_percent=None,
            proposed_duration=None,
            proposed_enrollment=None,
            targeting_config_slug=None,
            total_enrolled_clients=0,
        )
        serializer = NimbusAudienceUpdateSerializer(
            experiment,
            {
                "channels": [NimbusConstants.Channel.DESKTOP_BETA.value],
                "firefox_min_version": NimbusConstants.Version.FIREFOX_80.value,
                "population_percent": 10,
                "proposed_duration": 42,
                "proposed_enrollment": 120,
                "targeting_config_slug": (
                    NimbusConstants.TargetingConfig.ALL_ENGLISH.value
                ),
                "total_enrolled_clients": 100,
            },
            context={"user": user},
        )
        self.assertEqual(experiment.changes.count(), 0)
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()
        self.assertEqual(experiment.changes.count(), 1)
        self.assertEqual(
            experiment.channels, [NimbusConstants.Channel.DESKTOP_BETA.value]
        )
        self.assertEqual(
            experiment.firefox_min_version, NimbusConstants.Version.FIREFOX_80.value
        )
        self.assertEqual(experiment.population_percent, 10)
        self.assertEqual(experiment.proposed_duration, 42)
        self.assertEqual(experiment.proposed_enrollment, 120)
        self.assertEqual(
            experiment.targeting_config_slug,
            NimbusConstants.TargetingConfig.ALL_ENGLISH.value,
        )
        self.assertEqual(experiment.total_enrolled_clients, 100)

    def test_serializer_updates_audience_on_experiment_invalid_channels(self):
        user = UserFactory()
        experiment = NimbusExperimentFactory(
            channels=[],
            application=NimbusExperiment.Application.FENIX,
            firefox_min_version=None,
            population_percent=None,
            proposed_duration=None,
            proposed_enrollment=None,
            targeting_config_slug=None,
            total_enrolled_clients=0,
        )
        serializer = NimbusAudienceUpdateSerializer(
            experiment,
            {
                "channels": [NimbusConstants.Channel.DESKTOP_BETA.value],
                "firefox_min_version": NimbusConstants.Version.FIREFOX_80.value,
                "population_percent": 10,
                "proposed_duration": 42,
                "proposed_enrollment": 120,
                "targeting_config_slug": (
                    NimbusConstants.TargetingConfig.ALL_ENGLISH.value
                ),
                "total_enrolled_clients": 100,
            },
            context={"user": user},
        )
        self.assertEqual(experiment.changes.count(), 0)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {"channels": ["Invalid channels for experiment application."]},
        )


class TestNimbusStatusUpdateSerializer(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_status_update(self):
        experiment = NimbusExperimentFactory(status=NimbusExperiment.Status.DRAFT)
        serializer = NimbusStatusUpdateSerializer(
            experiment,
            data={"status": NimbusExperiment.Status.REVIEW},
            context={"user": self.user},
        )
        self.assertEqual(experiment.changes.count(), 0)
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()
        self.assertEqual(experiment.changes.count(), 1)
        self.assertEqual(experiment.status, NimbusExperiment.Status.REVIEW)

    def test_status_with_invalid_target_status(self):
        experiment = NimbusExperimentFactory(status=NimbusExperiment.Status.DRAFT)
        serializer = NimbusStatusUpdateSerializer(
            experiment,
            data={"status": NimbusExperiment.Status.ACCEPTED},
            context={"user": self.user},
        )
        self.assertEqual(experiment.changes.count(), 0)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {"status": ["Nimbus Experiments can only transition from DRAFT to REVIEW."]},
        )

    def test_status_with_invalid_existing_status(self):
        experiment = NimbusExperimentFactory(status=NimbusExperiment.Status.ACCEPTED)
        serializer = NimbusStatusUpdateSerializer(
            experiment,
            data={"status": NimbusExperiment.Status.REVIEW},
            context={"user": self.user},
        )
        self.assertEqual(experiment.changes.count(), 0)
        self.assertFalse(serializer.is_valid())
        self.assert_(
            serializer.errors["experiment"][0].startswith("Nimbus Experiment has status")
        )


class TestNimbusReadyForReviewSerializer(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_valid_experiment(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP.value,
            feature_config=NimbusFeatureConfigFactory(
                application=NimbusExperiment.Application.DESKTOP.value
            ),
        )
        serializer = NimbusReadyForReviewSerializer(
            experiment,
            data=NimbusReadyForReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

    def test_invalid_experiment_default_hypothesis(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP.value,
            feature_config=NimbusFeatureConfigFactory(
                application=NimbusExperiment.Application.DESKTOP.value
            ),
        )
        experiment.hypothesis = NimbusExperiment.HYPOTHESIS_DEFAULT
        experiment.save()
        serializer = NimbusReadyForReviewSerializer(
            experiment,
            data=NimbusReadyForReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors, {"hypothesis": ["Hypothesis cannot be the default value."]}
        )

    def test_invalid_experiment_requires_reference_branch(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP.value,
            feature_config=NimbusFeatureConfigFactory(
                application=NimbusExperiment.Application.DESKTOP.value
            ),
        )
        experiment.reference_branch = None
        experiment.save()
        serializer = NimbusReadyForReviewSerializer(
            experiment,
            data=NimbusReadyForReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {"reference_branch": ["This field may not be null."]},
        )
