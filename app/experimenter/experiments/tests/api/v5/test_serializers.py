from decimal import Decimal

import mock
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils.text import slugify
from parameterized import parameterized

from experimenter.base.tests.factories import CountryFactory, LocaleFactory
from experimenter.experiments.api.v5.serializers import (
    NimbusBranchReadyForReviewSerializer,
    NimbusBranchSerializer,
    NimbusExperimentCloneSerializer,
    NimbusExperimentSerializer,
    NimbusReadyForReviewSerializer,
)
from experimenter.experiments.changelog_utils.nimbus import generate_nimbus_changelog
from experimenter.experiments.constants.nimbus import NimbusConstants
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.models.nimbus import NimbusBranch, NimbusBucketRange
from experimenter.experiments.tests.factories import (
    TINY_PNG,
    NimbusBranchFactory,
    NimbusBranchScreenshotFactory,
    NimbusExperimentFactory,
)
from experimenter.experiments.tests.factories.nimbus import NimbusFeatureConfigFactory
from experimenter.openidc.tests.factories import UserFactory
from experimenter.outcomes import Outcomes
from experimenter.outcomes.tests import mock_valid_outcomes

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
            "feature_value": "{}",
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
            {"feature_value": ["A value must be supplied for an enabled feature."]},
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

    def test_branch_with_invalid_feature_value_json(self):
        branch_data = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "feature_enabled": True,
            "feature_value": "invalid json",
        }
        branch_serializer = NimbusBranchReadyForReviewSerializer(data=branch_data)
        self.assertFalse(branch_serializer.is_valid())
        self.assertIn("feature_value", branch_serializer.errors)

    def test_branch_update_screenshots(self):
        branch = NimbusBranchFactory()
        existing_screenshot = branch.screenshots.first()
        existing_image = existing_screenshot.image
        deleted_screenshots = [
            NimbusBranchScreenshotFactory.create(branch=branch),
            NimbusBranchScreenshotFactory.create(branch=branch),
            NimbusBranchScreenshotFactory.create(branch=branch),
        ]

        updated_screenshot_data = {
            "id": existing_screenshot.id,
            "description": "01 updated",
        }
        image_content = TINY_PNG
        new_screenshot_data = {
            "description": "02 new screenshot",
            "image": SimpleUploadedFile(name="Capture.PNG", content=image_content),
        }
        branch_data = {
            "name": "updated name",
            "description": "updated description",
            "ratio": 1,
            "screenshots": [
                updated_screenshot_data,
                new_screenshot_data,
            ],
        }
        branch_serializer = NimbusBranchSerializer(branch, data=branch_data)
        self.assertTrue(branch_serializer.is_valid(), branch_serializer.errors)
        branch_serializer.save()

        branch = NimbusBranch.objects.get(pk=branch.id)
        self.assertEqual(branch.screenshots.count(), 2)

        for screenshot in deleted_screenshots:
            self.assertFalse(branch.screenshots.filter(pk=screenshot.id).exists())

        screenshots = branch.screenshots.order_by("description")
        updated_screenshot = screenshots[0]
        self.assertEqual(
            updated_screenshot.description, updated_screenshot_data["description"]
        )
        self.assertEqual(updated_screenshot.image.name, existing_image.name)

        new_screenshot = screenshots[1]
        self.assertEqual(new_screenshot.description, new_screenshot_data["description"])
        self.assertTrue(bool(new_screenshot.image))
        with new_screenshot.image.open() as image_file:
            self.assertEqual(image_file.read(), image_content)


class TestNimbusExperimentDocumentationLinkMixin(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_serializer_update_links(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
        )
        data = {
            "changelog_message": "test changelog message",
            "public_description": "changed",
            "documentation_links": [
                {
                    "title": NimbusExperiment.DocumentationLink.DS_JIRA,
                    "link": "https://example.com/1",
                },
                {
                    "title": NimbusExperiment.DocumentationLink.ENG_TICKET,
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
        data = {
            "public_description": "changed",
            "changelog_message": "test changelog message",
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assert_documentation_links(experiment.id, links_before)

    def test_serializer_preserves_links_with_branch_update(self):
        """
        Reproduction for EXP-1788: branch update deleted documentation
        links. Topically more appropriate for the branch serializer suite,
        but the links assert method lives here
        """
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
        data = {
            "public_description": "changed reference",
            "reference_branch": {
                "description": "changed",
                "feature_enabled": False,
                "name": "also changed reference",
                "ratio": 1,
            },
            "treatment_branches": [
                {
                    "description": "changed treatment",
                    "feature_enabled": False,
                    "name": "also changed treatment",
                    "ratio": 1,
                },
            ],
            "changelog_message": "test changelog message",
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.assert_documentation_links(experiment.id, links_before)

    def test_serializer_supports_multiple_links_of_same_type(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
        )
        data = {
            "changelog_message": "test changelog message",
            "public_description": "changed",
            "documentation_links": [
                {
                    "title": NimbusExperiment.DocumentationLink.ENG_TICKET,
                    "link": "https://example.com/1",
                },
                {
                    "title": NimbusExperiment.DocumentationLink.ENG_TICKET,
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

    def test_serializer_replace_branches(self):
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
            "changelog_message": "test changelog message",
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

    def test_serializer_update_branches_with_ids(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.FENIX,
        )
        NimbusBranchFactory.create(experiment=experiment)
        NimbusBranchFactory.create(experiment=experiment)
        NimbusBranchFactory.create(experiment=experiment)

        orig_reference_branch = experiment.reference_branch
        orig_treatment_branch = experiment.treatment_branches[0]
        deleted_branches = experiment.treatment_branches[1:]

        updated_reference_branch_data = {
            "id": orig_reference_branch.id,
            "name": "control",
            "description": "updated reference description",
            "ratio": 1,
        }
        updated_treatment_branch_data = {
            "id": orig_treatment_branch.id,
            "name": "treatment",
            "description": "updated treatment description",
            "ratio": 1,
        }
        added_treatment_branch_data = {
            "name": "treatment 2",
            "description": "new treatment branch",
            "ratio": 1,
        }
        data = {
            "id": experiment.id,
            "changelog_message": "edited branches",
            "reference_branch": updated_reference_branch_data,
            "treatment_branches": [
                updated_treatment_branch_data,
                added_treatment_branch_data,
            ],
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        experiment = NimbusExperiment.objects.get(id=experiment.id)

        self.assertEqual(experiment.branches.count(), 3)
        for deleted_branch in deleted_branches:
            self.assertFalse(experiment.branches.filter(pk=deleted_branch.id).exists())
        self.assertEqual(experiment.reference_branch.id, orig_reference_branch.id)
        self.assertEqual(
            experiment.reference_branch.description,
            updated_reference_branch_data["description"],
        )
        self.assertEqual(experiment.treatment_branches[0].id, orig_treatment_branch.id)
        self.assertEqual(
            experiment.reference_branch.description,
            updated_reference_branch_data["description"],
        )
        self.assertEqual(
            experiment.treatment_branches[1].description,
            added_treatment_branch_data["description"],
        )

    def test_serializer_feature_config_validation(self):
        feature_config = NimbusFeatureConfigFactory.create(
            schema=self.BASIC_JSON_SCHEMA, application=NimbusExperiment.Application.IOS
        )
        experiment = NimbusExperimentFactory(
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.IOS,
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
            "changelog_message": "test changelog message",
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

    def test_does_not_delete_branches_when_other_fields_specified(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        branch_count = experiment.branches.count()

        serializer = NimbusExperimentSerializer(
            instance=experiment,
            data={
                "name": "new name",
                "changelog_message": "test changelog message",
            },
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
            "changelog_message": "test changelog message",
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
        )
        data = {
            "name": "",
            "hypothesis": "",
            "public_description": "",
            "feature_config": None,
            "treatment_branches": [],
            "primary_outcomes": [],
            "secondary_outcomes": [],
            "channel": NimbusExperiment.Channel.NO_CHANNEL,
            "firefox_min_version": NimbusExperiment.Version.NO_VERSION,
            "population_percent": "0.0",
            "proposed_duration": 0,
            "proposed_enrollment": 0,
            "targeting_config_slug": NimbusExperiment.TargetingConfig.NO_TARGETING,
            "total_enrolled_clients": 0,
            "changelog_message": "test changelog message",
            "countries": [],
            "locales": [],
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
        self.assertEqual(experiment.primary_outcomes, [])
        self.assertEqual(experiment.secondary_outcomes, [])
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
        self.assertEqual(list(experiment.countries.all()), [])
        self.assertEqual(list(experiment.locales.all()), [])

    def test_serializer_creates_experiment_and_sets_slug_and_owner(self):
        data = {
            "name": "Test 1234",
            "hypothesis": "Test hypothesis",
            "application": NimbusExperiment.Application.DESKTOP,
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
        self.assertEqual(experiment.public_description, data["public_description"])
        # Owner should match the email of the user who created the experiment
        self.assertEqual(experiment.owner, self.user)

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
        country = CountryFactory.create()
        locale = LocaleFactory.create()
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
                "channel": NimbusConstants.Channel.BETA,
                "firefox_min_version": NimbusConstants.Version.FIREFOX_83,
                "population_percent": 10,
                "proposed_duration": 120,
                "proposed_enrollment": 42,
                "targeting_config_slug": (
                    NimbusConstants.TargetingConfig.TARGETING_FIRST_RUN
                ),
                "total_enrolled_clients": 100,
                "changelog_message": "test changelog message",
                "countries": [country.id],
                "locales": [locale.id],
            },
            context={"user": self.user},
        )
        self.assertEqual(experiment.changes.count(), 0)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        experiment = serializer.save()
        self.assertEqual(experiment.changes.count(), 1)
        self.assertEqual(experiment.channel, NimbusConstants.Channel.BETA)
        self.assertEqual(
            experiment.firefox_min_version, NimbusConstants.Version.FIREFOX_83
        )
        self.assertEqual(experiment.population_percent, 10)
        self.assertEqual(experiment.proposed_duration, 120)
        self.assertEqual(experiment.proposed_enrollment, 42)
        self.assertEqual(
            experiment.targeting_config_slug,
            NimbusConstants.TargetingConfig.TARGETING_FIRST_RUN,
        )
        self.assertEqual(experiment.total_enrolled_clients, 100)
        self.assertEqual(list(experiment.countries.all()), [country])
        self.assertEqual(list(experiment.locales.all()), [locale])

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

    def test_status_restriction(self):
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

    def test_status_generates_bucket_allocation(self):
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

    def test_publish_status_generates_bucket_allocation(self):
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
            [NimbusExperiment.PublishStatus.IDLE],
            [NimbusExperiment.PublishStatus.REVIEW],
        ]
    )
    def test_update_publish_status_doesnt_invoke_push_task(self, publish_status):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
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
        NimbusConstants.MAX_PRIMARY_OUTCOMES = 1

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

    def test_can_review_for_requesting_user_when_idle(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": NimbusExperiment.PublishStatus.APPROVED,
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

    def test_targeting_config_for_correct_application(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        data = {
            "targeting_config_slug": (
                NimbusExperiment.TargetingConfig.TARGETING_FIRST_RUN_WINDOWS_1903_NEWER
            ),
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
            "targeting_config_slug": (
                NimbusExperiment.TargetingConfig.TARGETING_FIRST_RUN_WINDOWS_1903_NEWER
            ),
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


class TestNimbusReadyForReviewSerializer(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_valid_experiment(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_config=NimbusFeatureConfigFactory(
                application=NimbusExperiment.Application.DESKTOP
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
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_config=NimbusFeatureConfigFactory(
                application=NimbusExperiment.Application.DESKTOP
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
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_config=NimbusFeatureConfigFactory(
                application=NimbusExperiment.Application.DESKTOP
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
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_config=NimbusFeatureConfigFactory(
                application=NimbusExperiment.Application.DESKTOP
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
            {"reference_branch": {"description": [NimbusConstants.ERROR_REQUIRED_FIELD]}},
        )

    def test_invalid_experiment_requires_non_zero_population_percent(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            population_percent=0.0,
            application=NimbusExperiment.Application.DESKTOP,
            feature_config=NimbusFeatureConfigFactory(
                application=NimbusExperiment.Application.DESKTOP
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
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            str(serializer.errors["population_percent"][0]),
            "Ensure this value is greater than or equal to 0.0001.",
        )

    def test_valid_experiment_minimum_population_percent(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            population_percent=0.0001,
            application=NimbusExperiment.Application.DESKTOP,
            feature_config=NimbusFeatureConfigFactory(
                application=NimbusExperiment.Application.DESKTOP
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
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_experiment_treatment_branch_requires_description(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_config=NimbusFeatureConfigFactory(
                application=NimbusExperiment.Application.DESKTOP
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
            {"description": [NimbusConstants.ERROR_REQUIRED_FIELD]},
        )

    def test_invalid_experiment_missing_feature_config(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_config=None,
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
            serializer.errors["feature_config"],
            [NimbusConstants.ERROR_REQUIRED_FEATURE_CONFIG],
        )

    def test_invalid_experiment_risk_questions(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            risk_partner_related=None,
            risk_revenue=None,
            risk_brand=None,
            application=NimbusExperiment.Application.DESKTOP,
            feature_config=NimbusFeatureConfigFactory(
                application=NimbusExperiment.Application.DESKTOP
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
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            str(serializer.errors["risk_partner_related"][0]),
            NimbusConstants.ERROR_REQUIRED_QUESTION,
        )
        self.assertEqual(
            str(serializer.errors["risk_revenue"][0]),
            NimbusConstants.ERROR_REQUIRED_QUESTION,
        )
        self.assertEqual(
            str(serializer.errors["risk_brand"][0]),
            NimbusConstants.ERROR_REQUIRED_QUESTION,
        )

    @parameterized.expand(
        [
            (True, NimbusExperiment.Application.DESKTOP),
            (False, NimbusExperiment.Application.FENIX),
            (False, NimbusExperiment.Application.IOS),
        ]
    )
    def test_channel_required_for_mobile(self, expected_valid, application):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            feature_config=NimbusFeatureConfigFactory(application=application),
        )

        serializer = NimbusReadyForReviewSerializer(
            experiment,
            data=NimbusReadyForReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertEqual(serializer.is_valid(), expected_valid, serializer.errors)
        if not expected_valid:
            self.assertIn("channel", serializer.errors)

    def test_serializer_feature_config_validation_application_mismatches_error(self):
        experiment = NimbusExperimentFactory(
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.FENIX,
            channel=NimbusExperiment.Channel.RELEASE,
            feature_config=NimbusFeatureConfigFactory.create(
                schema=BASIC_JSON_SCHEMA,
                application=NimbusExperiment.Application.IOS,
            ),
        )
        experiment.reference_branch.feature_value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        experiment.save()
        treatment_branch = experiment.treatment_branches[0]
        treatment_branch.feature_value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        treatment_branch.save()

        serializer = NimbusReadyForReviewSerializer(
            experiment,
            data=NimbusReadyForReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        import logging

        logging.info(serializer.errors)
        self.assertEqual(
            serializer.errors,
            {
                "feature_config": [
                    "Feature Config application ios does not "
                    "match experiment application fenix."
                ]
            },
        )

    def test_serializer_feature_config_validation_missing_feature_config(self):
        experiment = NimbusExperimentFactory(
            status=NimbusExperiment.Status.DRAFT,
            feature_config=None,
        )
        experiment.reference_branch.feature_value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        experiment.save()
        treatment_branch = experiment.treatment_branches[0]
        treatment_branch.feature_value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        treatment_branch.save()

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
            serializer.errors["feature_config"][0],
            "You must select a feature configuration from the drop down.",
        )
        self.assertEqual(len(serializer.errors), 1)

    def test_serializer_feature_config_validation_bad_json_value(self):
        experiment = NimbusExperimentFactory(
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            feature_config=NimbusFeatureConfigFactory.create(
                schema=BASIC_JSON_SCHEMA,
                application=NimbusExperiment.Application.DESKTOP,
            ),
        )
        experiment.reference_branch.feature_value = """\
            {"directMigrateSingleProfile: true
        """.strip()
        experiment.save()
        treatment_branch = experiment.treatment_branches[0]
        treatment_branch.feature_value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        treatment_branch.save()

        serializer = NimbusReadyForReviewSerializer(
            experiment,
            data=NimbusReadyForReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "Unterminated string",
            serializer.errors["reference_branch"]["feature_value"][0],
        )
        self.assertEqual(len(serializer.errors), 1)

    def test_serializer_feature_config_validation_reference_value_schema_error(self):
        experiment = NimbusExperimentFactory(
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            feature_config=NimbusFeatureConfigFactory.create(
                schema=BASIC_JSON_SCHEMA,
                application=NimbusExperiment.Application.DESKTOP,
            ),
        )
        experiment.reference_branch.feature_value = """\
            {"DDirectMigrateSingleProfile": true}
        """.strip()
        experiment.save()
        treatment_branch = experiment.treatment_branches[0]
        treatment_branch.feature_value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        treatment_branch.save()

        serializer = NimbusReadyForReviewSerializer(
            experiment,
            data=NimbusReadyForReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assert_(
            serializer.errors["reference_branch"]["feature_value"][0].startswith(
                "Additional properties are not allowed"
            )
        )
        self.assertEqual(len(serializer.errors), 1)

    def test_serializer_feature_config_validation_treatment_value_schema_error(self):
        experiment = NimbusExperimentFactory(
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            feature_config=NimbusFeatureConfigFactory.create(
                schema=BASIC_JSON_SCHEMA,
                application=NimbusExperiment.Application.DESKTOP,
            ),
        )
        experiment.reference_branch.feature_value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        experiment.save()
        treatment_branch = experiment.treatment_branches[0]
        treatment_branch.feature_value = """\
            {"DDirectMigrateSingleProfile": true}
        """.strip()
        treatment_branch.save()

        serializer = NimbusReadyForReviewSerializer(
            experiment,
            data=NimbusReadyForReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assert_(
            serializer.errors["treatment_branches"][0]["feature_value"][0].startswith(
                "Additional properties are not allowed"
            )
        )
        self.assertEqual(len(serializer.errors), 1)


class TestNimbusStatusTransitionValidator(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_update_experiment_status_error(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status": NimbusExperiment.Status.LIVE,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["status"][0],
            "Nimbus Experiment status cannot transition from Draft to Live.",
        )

    def test_update_publish_status_from_approved_to_review_error(self):
        experiment = NimbusExperimentFactory.create(
            publish_status=NimbusExperiment.PublishStatus.APPROVED,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": NimbusExperiment.PublishStatus.REVIEW,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["publish_status"][0],
            "Nimbus Experiment publish_status cannot transition from Approved to Review.",
        )


class TestNimbusStatusValidationMixin(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_update_experiment_publish_status_while_in_preview(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.PREVIEW,
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

    def test_update_experiment_with_invalid_status_error(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.PREVIEW,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "public_description": "who knows, really",
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("experiment", serializer.errors)

    def test_update_experiment_with_invalid_publish_status_error(self):
        experiment = NimbusExperimentFactory.create(
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "public_description": "who knows, really",
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("experiment", serializer.errors)


class TestNimbusExperimentCloneSerializer(TestCase):
    def test_clones_experiment(self):
        parent = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )
        serializer = NimbusExperimentCloneSerializer(
            data={
                "parent_slug": parent.slug,
                "name": "New Name",
            },
            context={"user": parent.owner},
        )
        self.assertTrue(serializer.is_valid())
        child = serializer.save()
        self.assertEqual(child.name, "New Name")
        self.assertEqual(child.slug, "new-name")
        self.assertEqual(child.parent, parent)

    def test_invalid_parent_slug(self):
        user = UserFactory.create()
        serializer = NimbusExperimentCloneSerializer(
            data={
                "parent_slug": "bad slug",
                "name": "New Name",
            },
            context={"user": user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("parent_slug", serializer.errors)

    def test_invalid_with_duplicate_name(self):
        parent = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )
        serializer = NimbusExperimentCloneSerializer(
            data={
                "parent_slug": parent.slug,
                "name": parent.name,
            },
            context={"user": parent.owner},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_invalid_with_long_name(self):
        parent = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )
        serializer = NimbusExperimentCloneSerializer(
            data={
                "parent_slug": parent.slug,
                "name": "a" * 81,
            },
            context={"user": parent.owner},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)
