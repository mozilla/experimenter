from decimal import Decimal

from django.test import TestCase
from django.utils.text import slugify
from parameterized import parameterized

from experimenter.experiments.api.v5.serializers import (
    NimbusBranchSerializer,
    NimbusExperimentSerializer,
    NimbusReadyForReviewSerializer,
)
from experimenter.experiments.constants.nimbus import NimbusConstants
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.models.nimbus import (
    NimbusBucketRange,
    NimbusFeatureConfig,
)
from experimenter.experiments.tests.factories import (
    NimbusBranchFactory,
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
            "risk_mitigation_link": "https://example.com/risk",
            "public_description": "Test description",
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

    def test_serializer_accepts_blank_risk_mitigation_link(self):
        data = {
            "name": "Test 1234",
            "hypothesis": "Test hypothesis",
            "application": NimbusExperiment.Application.DESKTOP.value,
            "public_description": "Test description",
            "risk_mitigation_link": "",
        }
        serializer = NimbusExperimentSerializer(data=data, context={"user": self.user})
        self.assertTrue(serializer.is_valid())

    def test_serializer_rejects_bad_name(self):
        data = {
            "name": "&^%&^%&^%&^%^&%^&",
            "hypothesis": "Test hypothesis",
            "application": NimbusExperiment.Application.DESKTOP.value,
            "public_description": "Test description",
        }

        serializer = NimbusExperimentSerializer(data=data, context={"user": self.user})
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
            "application": NimbusExperiment.Application.DESKTOP.value,
            "public_description": "Test description",
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


class TestNimbusExperimentDocumentationLinkMixin(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_serializer_update_links(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
        )
        data = {
            "public_description": "changed",
            "documentation_links": [
                {
                    "title": NimbusExperiment.DocumentationLink.DS_JIRA.value,
                    "link": "https://example.com/1",
                },
                {
                    "title": NimbusExperiment.DocumentationLink.ENG_TICKET.value,
                    "link": "https://example.com/2",
                },
            ],
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assert_documentation_links(experiment.id, data["documentation_links"])

    def test_serializer_preserves_links_when_absent_in_data(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
        )
        links_before = []
        for link in experiment.documentation_links.all():
            links_before.append(
                {
                    "title": link.title,
                    "link": link.link,
                }
            )
        data = {"public_description": "changed"}
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assert_documentation_links(experiment.id, links_before)

    def assert_documentation_links(self, experiment_id, links_data):
        experiment = NimbusExperiment.objects.get(id=experiment_id)
        documentation_links = experiment.documentation_links.all()
        for key in (
            "title",
            "link",
        ):
            self.assertEqual(
                {b[key] for b in links_data},
                {getattr(b, key) for b in documentation_links},
            )


class TestNimbusExperimentBranchMixin(TestCase):
    maxDiff = None
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
            {"name": "treatment2", "description": "desc2", "ratio": 1},
        ]

        data = {
            "feature_config": None,
            "reference_branch": reference_branch,
            "treatment_branches": treatment_branches,
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        experiment = NimbusExperiment.objects.get(id=experiment.id)

        for key, val in reference_branch.items():
            self.assertEqual(getattr(experiment.reference_branch, key), val)

        for branch_data in treatment_branches:
            branch = experiment.branches.get(name=branch_data["name"])
            for key, val in branch_data.items():
                self.assertEqual(getattr(branch, key), val)

    def test_serializer_feature_config_validation(self):
        feature_config = NimbusFeatureConfigFactory.create(schema=self.BASIC_JSON_SCHEMA)
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
                "name": "treatment2",
                "description": "desc2",
                "ratio": 1,
                "feature_enabled": True,
                "feature_value": treatment_feature_value,
            },
        ]

        data = {
            "feature_config": feature_config.id,
            "reference_branch": reference_branch,
            "treatment_branches": treatment_branches,
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )

        self.assertTrue(serializer.is_valid())
        serializer.save()
        experiment = NimbusExperiment.objects.get(id=experiment.id)

        for key, val in reference_branch.items():
            self.assertEqual(getattr(experiment.reference_branch, key), val)

        for branch_data in treatment_branches:
            branch = experiment.branches.get(name=branch_data["name"])
            for key, val in branch_data.items():
                self.assertEqual(getattr(branch, key), val)

    def test_serializer_feature_config_validation_reference_value_schema_error(self):
        feature_config = NimbusFeatureConfigFactory.create(schema=self.BASIC_JSON_SCHEMA)
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

        data = {
            "feature_config": feature_config.id,
            "reference_branch": reference_branch,
            "treatment_branches": treatment_branches,
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertFalse(serializer.is_valid())
        self.assert_(
            serializer.errors["reference_branch"]["feature_value"][0].startswith(
                "Additional properties are not allowed"
            )
        )
        self.assertEqual(len(serializer.errors), 1)

    def test_serializer_feature_config_validation_bad_json_value(self):
        feature_config = NimbusFeatureConfig(schema=self.BASIC_JSON_SCHEMA)
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

        data = {
            "feature_config": feature_config.id,
            "reference_branch": reference_branch,
            "treatment_branches": treatment_branches,
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertFalse(serializer.is_valid())
        self.assert_(
            serializer.errors["reference_branch"]["feature_value"][0].startswith(
                "Unterminated string"
            )
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

        data = {
            "reference_branch": reference_branch,
            "treatment_branches": treatment_branches,
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["feature_config"][0],
            "Feature Config required when a branch has feature enabled.",
        )
        self.assertEqual(len(serializer.errors), 1)

    def test_serializer_feature_config_validation_treatment_value_schema_error(self):
        feature_config = NimbusFeatureConfig(schema=self.BASIC_JSON_SCHEMA)
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

        data = {
            "feature_config": feature_config.id,
            "reference_branch": reference_branch,
            "treatment_branches": treatment_branches,
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertFalse(serializer.is_valid())
        self.assert_(
            serializer.errors["treatment_branches"][1]["feature_value"][0].startswith(
                "Additional properties are not allowed"
            )
        )
        self.assertEqual(len(serializer.errors), 1)

    def test_does_not_delete_branches_when_other_fields_specified(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT
        )
        branch_count = experiment.branches.count()

        serializer = NimbusExperimentSerializer(
            instance=experiment,
            data={"name": "new name"},
            context={"user": UserFactory()},
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.branches.count(), branch_count)
        self.assertEqual(experiment.name, "new name")

    def test_no_duplicate_branch_names(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
        )

        reference_branch = {"name": "control", "description": "a control", "ratio": 1}
        treatment_branches = [
            {"name": "control", "description": "desc1", "ratio": 1},
        ]

        data = {
            "feature_config": None,
            "reference_branch": reference_branch,
            "treatment_branches": treatment_branches,
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "reference_branch": {"name": NimbusConstants.ERROR_DUPLICATE_BRANCH_NAME},
                "treatment_branches": [
                    {"name": NimbusConstants.ERROR_DUPLICATE_BRANCH_NAME}
                    for i in data["treatment_branches"]
                ],
            },
        )


class TestNimbusExperimentProbeSetMixin(TestCase):
    def test_serializer_updates_probe_sets_on_experiment(self):
        user = UserFactory()
        experiment = NimbusExperimentFactory(probe_sets=[])
        primary_probe_set_slugs = [
            NimbusProbeSetFactory().slug
            for i in range(NimbusExperiment.MAX_PRIMARY_PROBE_SETS)
        ]
        secondary_probe_set_slugs = [NimbusProbeSetFactory().slug for i in range(3)]

        serializer = NimbusExperimentSerializer(
            experiment,
            {
                "primary_probe_set_slugs": primary_probe_set_slugs,
                "secondary_probe_set_slugs": secondary_probe_set_slugs,
            },
            context={"user": user},
        )

        self.assertEqual(experiment.changes.count(), 0)
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()
        self.assertEqual(experiment.changes.count(), 1)

        self.assertEqual(
            set(primary_probe_set_slugs) | set(secondary_probe_set_slugs),
            set(experiment.probe_sets.all().values_list("slug", flat=True)),
        )
        self.assertEqual(
            set([p.slug for p in experiment.primary_probe_sets]),
            set(primary_probe_set_slugs),
        )
        self.assertEqual(
            set([p.slug for p in experiment.secondary_probe_sets]),
            set(secondary_probe_set_slugs),
        )

    def test_serializer_rejects_duplicate_probes(self):
        user = UserFactory()
        experiment = NimbusExperimentFactory(probe_sets=[])
        probe_sets = [NimbusProbeSetFactory() for i in range(3)]

        serializer = NimbusExperimentSerializer(
            experiment,
            {
                "primary_probe_set_slugs": [
                    p.slug for p in probe_sets[: NimbusExperiment.MAX_PRIMARY_PROBE_SETS]
                ],
                "secondary_probe_set_slugs": [p.slug for p in probe_sets],
            },
            context={"user": user},
        )

        self.assertEqual(experiment.changes.count(), 0)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(experiment.changes.count(), 0)
        self.assertEqual(
            serializer.errors["primary_probe_set_slugs"][0],
            "Primary probe sets cannot overlap with secondary probe sets.",
        )

    def test_serializer_rejects_too_many_primary_probe_sets(self):
        user = UserFactory()
        experiment = NimbusExperimentFactory(probe_sets=[])
        probe_sets = [NimbusProbeSetFactory() for i in range(3)]

        serializer = NimbusExperimentSerializer(
            experiment,
            {
                "primary_probe_set_slugs": [p.slug for p in probe_sets],
                "secondary_probe_set_slugs": [],
            },
            context={"user": user},
        )

        self.assertEqual(experiment.changes.count(), 0)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(experiment.changes.count(), 0)
        self.assertIn(
            "Exceeded maximum primary probe set limit of",
            serializer.errors["primary_probe_set_slugs"][0],
        )

    def test_does_not_delete_probesets_when_other_fields_specified(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT
        )
        probesets_count = experiment.probe_sets.count()

        serializer = NimbusExperimentSerializer(
            instance=experiment,
            data={"name": "new name"},
            context={"user": UserFactory()},
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.probe_sets.count(), probesets_count)
        self.assertEqual(experiment.name, "new name")


class TestNimbusExperimentSerializer(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_required_fields_for_creating_experiment(self):
        data = {
            "name": "",
            "hypothesis": NimbusExperiment.HYPOTHESIS_DEFAULT,
            "application": "",
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
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT
        )
        data = {
            "name": "",
            "hypothesis": "",
            "public_description": "",
            "feature_config": None,
            "treatment_branches": [],
            "primary_probe_set_slugs": [],
            "secondary_probe_set_slugs": [],
            "channel": NimbusExperiment.Channel.NO_CHANNEL,
            "firefox_min_version": NimbusExperiment.Version.NO_VERSION,
            "population_percent": "0.0",
            "proposed_duration": 0,
            "proposed_enrollment": 0,
            "targeting_config_slug": NimbusExperiment.TargetingConfig.NO_TARGETING,
            "total_enrolled_clients": 0,
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
        self.assertEqual(experiment.feature_config, None)
        self.assertEqual(experiment.treatment_branches, [])
        self.assertEqual(experiment.primary_probe_sets.count(), 0)
        self.assertEqual(experiment.secondary_probe_sets.count(), 0)
        self.assertEqual(experiment.channel, NimbusExperiment.Channel.NO_CHANNEL)
        self.assertEqual(
            experiment.firefox_min_version, NimbusExperiment.Version.NO_VERSION
        )
        self.assertEqual(experiment.population_percent, 0.0)
        self.assertEqual(experiment.proposed_duration, 0)
        self.assertEqual(experiment.proposed_enrollment, 0)
        self.assertEqual(
            experiment.targeting_config_slug,
            NimbusExperiment.TargetingConfig.NO_TARGETING,
        )
        self.assertEqual(experiment.total_enrolled_clients, 0)

    def test_serializer_creates_experiment_and_sets_slug_and_owner(self):
        data = {
            "name": "Test 1234",
            "hypothesis": "Test hypothesis",
            "application": NimbusExperiment.Application.DESKTOP.value,
            "public_description": "Test description",
        }

        serializer = NimbusExperimentSerializer(data=data, context={"user": self.user})
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

        serializer = NimbusExperimentSerializer(data=data, context={"user": self.user})
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
            "application": NimbusExperiment.Application.DESKTOP.value,
            "public_description": "Test description",
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

    def test_serializer_updates_audience_on_experiment(self):
        experiment = NimbusExperimentFactory(
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            population_percent=0.0,
            proposed_duration=0,
            proposed_enrollment=0,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            total_enrolled_clients=0,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            {
                "channel": NimbusConstants.Channel.BETA.value,
                "firefox_min_version": NimbusConstants.Version.FIREFOX_83.value,
                "population_percent": 10,
                "proposed_duration": 42,
                "proposed_enrollment": 120,
                "targeting_config_slug": (
                    NimbusConstants.TargetingConfig.ALL_ENGLISH.value
                ),
                "total_enrolled_clients": 100,
            },
            context={"user": self.user},
        )
        self.assertEqual(experiment.changes.count(), 0)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        experiment = serializer.save()
        self.assertEqual(experiment.changes.count(), 1)
        self.assertEqual(experiment.channel, NimbusConstants.Channel.BETA.value)
        self.assertEqual(
            experiment.firefox_min_version, NimbusConstants.Version.FIREFOX_83.value
        )
        self.assertEqual(experiment.population_percent, 10)
        self.assertEqual(experiment.proposed_duration, 42)
        self.assertEqual(experiment.proposed_enrollment, 120)
        self.assertEqual(
            experiment.targeting_config_slug,
            NimbusConstants.TargetingConfig.ALL_ENGLISH.value,
        )
        self.assertEqual(experiment.total_enrolled_clients, 100)

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
            {"population_percent": population_percent},
            context={"user": self.user},
        )
        self.assertEqual(serializer.is_valid(), expected_valid)
        if not expected_valid:
            self.assertIn("population_percent", serializer.errors)
        else:
            self.assertNotIn("population_percent", serializer.errors)

    def test_status_update_draft_to_review(self):
        experiment = NimbusExperimentFactory(status=NimbusExperiment.Status.DRAFT)
        serializer = NimbusExperimentSerializer(
            experiment,
            data={"status": NimbusExperiment.Status.REVIEW},
            context={"user": self.user},
        )
        self.assertEqual(experiment.changes.count(), 0)
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()
        self.assertEqual(experiment.changes.count(), 1)
        self.assertEqual(experiment.status, NimbusExperiment.Status.REVIEW)

    def test_status_update_draft_to_preview(self):
        experiment = NimbusExperimentFactory(status=NimbusExperiment.Status.DRAFT)
        serializer = NimbusExperimentSerializer(
            experiment,
            data={"status": NimbusExperiment.Status.PREVIEW},
            context={"user": self.user},
        )
        self.assertEqual(experiment.changes.count(), 0)
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()
        self.assertEqual(experiment.changes.count(), 1)
        self.assertEqual(experiment.status, NimbusExperiment.Status.PREVIEW)

    def test_status_update_preview_to_draft(self):
        experiment = NimbusExperimentFactory(status=NimbusExperiment.Status.PREVIEW)
        serializer = NimbusExperimentSerializer(
            experiment,
            data={"status": NimbusExperiment.Status.DRAFT},
            context={"user": self.user},
        )
        self.assertEqual(experiment.changes.count(), 0)
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()
        self.assertEqual(experiment.changes.count(), 1)
        self.assertEqual(experiment.status, NimbusExperiment.Status.DRAFT)

    def test_status_with_invalid_target_status(self):
        experiment = NimbusExperimentFactory(status=NimbusExperiment.Status.DRAFT)
        serializer = NimbusExperimentSerializer(
            experiment,
            data={"status": NimbusExperiment.Status.ACCEPTED},
            context={"user": self.user},
        )
        self.assertEqual(experiment.changes.count(), 0)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "status": [
                    "Nimbus Experiment status cannot transition from Draft to Accepted."
                ]
            },
            serializer.errors,
        )

    def test_name_change_with_live_status(self):
        experiment = NimbusExperimentFactory(status=NimbusExperiment.Status.LIVE)
        serializer = NimbusExperimentSerializer(
            experiment,
            data={"name": "new name"},
            context={"user": self.user},
        )
        self.assertEqual(experiment.changes.count(), 0)
        self.assertFalse(serializer.is_valid())
        self.assert_(
            serializer.errors["experiment"][0].startswith("Nimbus Experiment has status")
        )

    def test_name_change_with_preview_status(self):
        experiment = NimbusExperimentFactory(status=NimbusExperiment.Status.PREVIEW)
        serializer = NimbusExperimentSerializer(
            experiment,
            data={"name": "new name"},
            context={"user": self.user},
        )
        self.assertEqual(experiment.changes.count(), 0)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "experiment": [
                    "Nimbus Experiment has status 'Preview', only status "
                    "can be changed."
                ]
            },
            serializer.errors,
        )

    def test_status_to_review_generates_bucket_allocation(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT, population_percent=Decimal("50.0")
        )

        self.assertFalse(NimbusBucketRange.objects.filter(experiment=experiment).exists())

        serializer = NimbusExperimentSerializer(
            experiment,
            data={"status": NimbusExperiment.Status.REVIEW},
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()

        self.assertTrue(NimbusBucketRange.objects.filter(experiment=experiment).exists())
        self.assertEqual(experiment.bucket_range.count, 5000)


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
            serializer.errors,
            {"hypothesis": ["Hypothesis cannot be the default value."]},
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

    def test_invalid_experiment_reference_branch_requires_description(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP.value,
            feature_config=NimbusFeatureConfigFactory(
                application=NimbusExperiment.Application.DESKTOP.value
            ),
        )
        experiment.reference_branch.description = ""
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
            {"reference_branch": ["Description cannot be blank."]},
        )

    def test_invalid_experiment_requires_non_zero_population_percent(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            population_percent=0.0,
        )
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
            str(serializer.errors["population_percent"][0]),
            "Ensure this value is greater than or equal to 0.0001.",
        )

    def test_invalid_experiment_treatment_branch_requires_description(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP.value,
            feature_config=NimbusFeatureConfigFactory(
                application=NimbusExperiment.Application.DESKTOP.value
            ),
        )
        treatment_branch = NimbusBranchFactory.create(
            experiment=experiment, description=""
        )
        experiment.branches.add(treatment_branch)
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
            serializer.errors["treatment_branches"][1],
            ["Description cannot be blank."],
        )
