from django.test import TestCase

from experimenter.experiments.api.v5.serializers import NimbusExperimentSerializer
from experimenter.experiments.constants.nimbus import NimbusConstants
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
    NimbusBranchFactory,
    NimbusExperimentFactory,
)
from experimenter.experiments.tests.factories.nimbus import NimbusFeatureConfigFactory
from experimenter.openidc.tests.factories import UserFactory


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
        reference_branch_data = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "feature_enabled": True,
            "feature_value": reference_feature_value,
        }
        treatment_branches_data = [
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
            "reference_branch": reference_branch_data,
            "treatment_branches": treatment_branches_data,
            "changelog_message": "test changelog message",
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )

        self.assertTrue(serializer.is_valid())
        serializer.save()
        experiment = NimbusExperiment.objects.get(id=experiment.id)

        self.assertEqual(experiment.reference_branch.name, reference_branch_data["name"])
        self.assertEqual(
            experiment.reference_branch.description, reference_branch_data["description"]
        )
        self.assertEqual(
            experiment.reference_branch.ratio, reference_branch_data["ratio"]
        )
        self.assertEqual(
            experiment.reference_branch.feature_values.get().enabled,
            reference_branch_data["feature_enabled"],
        )
        self.assertEqual(
            experiment.reference_branch.feature_values.get().value,
            reference_branch_data["feature_value"],
        )

        for branch_data in treatment_branches_data:
            branch = experiment.branches.get(name=branch_data["name"])
            self.assertEqual(branch.name, branch_data["name"])
            self.assertEqual(
                branch.description,
                branch_data["description"],
            )
            self.assertEqual(branch.ratio, branch_data["ratio"])

            if "feature_enabled" in branch_data:
                self.assertEqual(
                    branch.feature_values.get().enabled,
                    branch_data["feature_enabled"],
                )

            if "feature_value" in branch_data:
                self.assertEqual(
                    branch.feature_values.get().value,
                    branch_data["feature_value"],
                )

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

    def test_no_treatment_branches_for_rollout(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
        )
        experiment.is_rollout = True
        experiment.save()
        for branch in experiment.treatment_branches:
            branch.delete()

        data = {
            "treatment_branches": [
                {"name": "treatment A", "description": "desc1", "ratio": 1},
                {"name": "treatment B", "description": "desc2", "ratio": 1},
            ],
            "changelog_message": "test changelog message",
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "treatment_branches": [
                    {"name": NimbusConstants.ERROR_SINGLE_BRANCH_FOR_ROLLOUT}
                    for i in data["treatment_branches"]
                ],
            },
        )
