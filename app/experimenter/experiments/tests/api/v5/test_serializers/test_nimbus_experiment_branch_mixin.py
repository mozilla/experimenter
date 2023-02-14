from django.test import TestCase

from experimenter.experiments.api.v5.serializers import NimbusExperimentSerializer
from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)
from experimenter.openidc.tests.factories import UserFactory


class TestNimbusExperimentBranchMixinSingleFeature(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_serializer_sets_feature_config_and_creates_branches(self):
        feature_config = NimbusFeatureConfigFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED, feature_configs=[]
        )
        experiment.delete_branches()

        reference_branch = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "feature_value": "",
        }
        treatment_branch = {
            "name": "treatment",
            "description": "a treatment",
            "ratio": 1,
            "feature_value": '{"value": true}',
        }

        data = {
            "feature_config": feature_config.id,
            "reference_branch": reference_branch,
            "treatment_branches": [treatment_branch],
            "changelog_message": "test changelog message",
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.feature_configs.get(), feature_config)

        self.assertEqual(experiment.reference_branch.name, "control")
        self.assertEqual(experiment.reference_branch.description, "a control")
        self.assertEqual(experiment.reference_branch.ratio, 1)
        self.assertEqual(
            experiment.reference_branch.feature_values.get().feature_config,
            feature_config,
        )
        self.assertEqual(experiment.reference_branch.feature_values.get().value, "")

        self.assertEqual(len(experiment.treatment_branches), 1)
        self.assertEqual(experiment.treatment_branches[0].name, "treatment")
        self.assertEqual(experiment.treatment_branches[0].description, "a treatment")
        self.assertEqual(experiment.treatment_branches[0].ratio, 1)
        self.assertEqual(
            experiment.treatment_branches[0].feature_values.get().feature_config,
            feature_config,
        )
        self.assertEqual(
            experiment.treatment_branches[0].feature_values.get().value, '{"value": true}'
        )

    def test_serializer_replace_branches(self):
        feature_config = NimbusFeatureConfigFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED, feature_configs=[]
        )
        branch_ids = set(experiment.branches.all().values_list("id", flat=True))

        reference_branch = {
            "name": "new control",
            "description": "a new control",
            "ratio": 1,
            "feature_value": "",
        }
        treatment_branch = {
            "name": "new treatment",
            "description": "a new treatment",
            "ratio": 1,
            "feature_value": '{"value": true}',
        }

        data = {
            "feature_config": feature_config.id,
            "reference_branch": reference_branch,
            "treatment_branches": [treatment_branch],
            "changelog_message": "test changelog message",
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.feature_configs.get(), feature_config)
        self.assertEqual(
            set(experiment.branches.all().values_list("id", flat=True)).intersection(
                branch_ids
            ),
            set(),
        )

        self.assertEqual(experiment.reference_branch.name, "new control")
        self.assertEqual(experiment.reference_branch.description, "a new control")
        self.assertEqual(experiment.reference_branch.ratio, 1)
        self.assertEqual(
            experiment.reference_branch.feature_values.get().feature_config,
            feature_config,
        )
        self.assertEqual(experiment.reference_branch.feature_values.get().value, "")

        self.assertEqual(len(experiment.treatment_branches), 1)
        self.assertEqual(experiment.treatment_branches[0].name, "new treatment")
        self.assertEqual(experiment.treatment_branches[0].description, "a new treatment")
        self.assertEqual(experiment.treatment_branches[0].ratio, 1)
        self.assertEqual(
            experiment.treatment_branches[0].feature_values.get().feature_config,
            feature_config,
        )
        self.assertEqual(
            experiment.treatment_branches[0].feature_values.get().value, '{"value": true}'
        )

    def test_serializer_update_branches_with_ids(self):
        feature_config = NimbusFeatureConfigFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED, feature_configs=[]
        )
        branch_ids = set(experiment.branches.all().values_list("id", flat=True))

        reference_branch = {
            "id": experiment.reference_branch.id,
            "name": "new control",
            "description": "a new control",
            "ratio": 1,
            "feature_value": "",
        }
        treatment_branch = {
            "id": experiment.treatment_branches[0].id,
            "name": "new treatment",
            "description": "a new treatment",
            "ratio": 1,
            "feature_value": '{"value": true}',
        }

        data = {
            "feature_config": feature_config.id,
            "reference_branch": reference_branch,
            "treatment_branches": [treatment_branch],
            "changelog_message": "test changelog message",
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.feature_configs.get(), feature_config)
        self.assertEqual(
            set(experiment.branches.all().values_list("id", flat=True)), branch_ids
        )

        self.assertEqual(experiment.reference_branch.name, "new control")
        self.assertEqual(experiment.reference_branch.description, "a new control")
        self.assertEqual(experiment.reference_branch.ratio, 1)
        self.assertEqual(
            experiment.reference_branch.feature_values.get().feature_config,
            feature_config,
        )
        self.assertEqual(experiment.reference_branch.feature_values.get().value, "")

        self.assertEqual(len(experiment.treatment_branches), 1)
        self.assertEqual(experiment.treatment_branches[0].name, "new treatment")
        self.assertEqual(experiment.treatment_branches[0].description, "a new treatment")
        self.assertEqual(experiment.treatment_branches[0].ratio, 1)
        self.assertEqual(
            experiment.treatment_branches[0].feature_values.get().feature_config,
            feature_config,
        )
        self.assertEqual(
            experiment.treatment_branches[0].feature_values.get().value, '{"value": true}'
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
                    for _ in (data.get("treatment_branches", []) or [])
                ],
            },
        )

    def test_swap_reference_with_treatment_branch_name(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
        )
        experiment.delete_branches()

        reference_branch = {"name": "control", "description": "a control", "ratio": 1}
        treatment_branches = [
            {"name": "treatment", "description": "desc1", "ratio": 1},
            {"name": "treatment b", "description": "desc1", "ratio": 1},
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
        self.assertEqual(experiment.branches.count(), 3)
        self.assertEqual(experiment.reference_branch.name, reference_branch["name"])
        treatment_branch = experiment.treatment_branches[0]
        self.assertEqual(treatment_branch.name, treatment_branches[0]["name"])

        swap_reference_branch = {
            "name": "treatment",
            "description": "a control",
            "ratio": 1,
        }
        swap_treatment_branches = [
            {"name": "control", "description": "desc1", "ratio": 1},
            {"name": "treatment b", "description": "desc1", "ratio": 1},
        ]

        data = {
            "feature_config": None,
            "reference_branch": swap_reference_branch,
            "treatment_branches": swap_treatment_branches,
            "changelog_message": "test changelog message",
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "reference_branch": {"name": NimbusConstants.ERROR_BRANCH_SWAP},
            },
        )

    def test_swap_reference_with_any_treatment_branch_name(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
        )
        experiment.delete_branches()

        reference_branch = {"name": "control", "description": "a control", "ratio": 1}
        treatment_branches = [
            {"name": "treatment", "description": "desc1", "ratio": 1},
            {"name": "treatment b", "description": "desc1", "ratio": 1},
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
        self.assertEqual(experiment.branches.count(), 3)
        self.assertEqual(experiment.reference_branch.name, reference_branch["name"])
        treatment_branch = experiment.treatment_branches[0]
        self.assertEqual(treatment_branch.name, treatment_branches[0]["name"])

        swap_reference_branch = {
            "name": "treatment b",
            "description": "a control",
            "ratio": 1,
        }
        swap_treatment_branches = [
            {"name": "treatment", "description": "desc1", "ratio": 1},
            {"name": "control", "description": "desc1", "ratio": 1},
        ]

        data = {
            "feature_config": None,
            "reference_branch": swap_reference_branch,
            "treatment_branches": swap_treatment_branches,
            "changelog_message": "test changelog message",
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "reference_branch": {"name": NimbusConstants.ERROR_BRANCH_SWAP},
            },
        )

    def test_swap_treatment_branch_name_with_other_treatment_branch(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
        )
        experiment.delete_branches()

        reference_branch = {"name": "control", "description": "a control", "ratio": 1}
        treatment_branches = [
            {"name": "treatment", "description": "desc1", "ratio": 1},
            {"name": "treatment b", "description": "desc2", "ratio": 1},
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
        self.assertEqual(experiment.branches.count(), 3)
        self.assertEqual(experiment.reference_branch.name, reference_branch["name"])
        treatment_branch = experiment.treatment_branches[0]
        self.assertEqual(treatment_branch.name, treatment_branches[0]["name"])

        swap_treatment_branches = [
            {"name": "treatment b", "description": "desc1", "ratio": 1},
            {"name": "treatment", "description": "desc2", "ratio": 1},
        ]

        data = {
            "feature_config": None,
            "reference_branch": reference_branch,
            "treatment_branches": swap_treatment_branches,
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
                    {"name": NimbusConstants.ERROR_BRANCH_SWAP}
                    for _ in (data.get("treatment_branches", []) or [])
                ],
            },
        )


class TestNimbusExperimentBranchMixinMultiFeature(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_serializer_sets_feature_config_and_creates_branches(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config1 = NimbusFeatureConfigFactory.create(application=application)
        feature_config2 = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[],
        )
        experiment.delete_branches()

        reference_branch = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "feature_values": [
                {"feature_config": feature_config1.id, "value": "{}"},
                {"feature_config": feature_config2.id, "value": "{}"},
            ],
        }
        treatment_branch = {
            "name": "treatment",
            "description": "a treatment",
            "ratio": 1,
            "feature_values": [
                {"feature_config": feature_config1.id, "value": "{}"},
                {"feature_config": feature_config2.id, "value": "{}"},
            ],
        }
        data = {
            "feature_configs": [feature_config1.id, feature_config2.id],
            "reference_branch": reference_branch,
            "treatment_branches": [treatment_branch],
            "changelog_message": "test changelog message",
        }

        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(
            set(experiment.feature_configs.all().values_list("id", flat=True)),
            {feature_config1.id, feature_config2.id},
        )

        self.assertEqual(experiment.reference_branch.name, "control")
        self.assertEqual(experiment.reference_branch.description, "a control")
        self.assertEqual(experiment.reference_branch.ratio, 1)
        self.assertEqual(
            set(
                experiment.reference_branch.feature_values.all().values_list(
                    "feature_config__id", flat=True
                )
            ),
            {feature_config1.id, feature_config2.id},
        )

        self.assertEqual(len(experiment.treatment_branches), 1)
        self.assertEqual(experiment.treatment_branches[0].name, "treatment")
        self.assertEqual(experiment.treatment_branches[0].description, "a treatment")
        self.assertEqual(experiment.treatment_branches[0].ratio, 1)
        self.assertEqual(
            set(
                experiment.treatment_branches[0]
                .feature_values.all()
                .values_list("feature_config__id", flat=True)
            ),
            {feature_config1.id, feature_config2.id},
        )

    def test_serializer_replace_branches(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config1 = NimbusFeatureConfigFactory.create(application=application)
        feature_config2 = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[],
        )
        branch_ids = set(experiment.branches.all().values_list("id", flat=True))

        reference_branch = {
            "name": "new control",
            "description": "a new control",
            "ratio": 2,
            "feature_values": [
                {"feature_config": feature_config1.id, "value": "{}"},
                {"feature_config": feature_config2.id, "value": "{}"},
            ],
        }
        treatment_branch = {
            "name": "new treatment",
            "description": "a new treatment",
            "ratio": 2,
            "feature_values": [
                {"feature_config": feature_config1.id, "value": "{}"},
                {"feature_config": feature_config2.id, "value": "{}"},
            ],
        }
        data = {
            "feature_configs": [feature_config1.id, feature_config2.id],
            "reference_branch": reference_branch,
            "treatment_branches": [treatment_branch],
            "changelog_message": "test changelog message",
        }

        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(
            set(experiment.feature_configs.all().values_list("id", flat=True)),
            {feature_config1.id, feature_config2.id},
        )
        self.assertEqual(
            set(experiment.branches.all().values_list("id", flat=True)).intersection(
                branch_ids
            ),
            set(),
        )

        self.assertEqual(experiment.reference_branch.name, "new control")
        self.assertEqual(experiment.reference_branch.description, "a new control")
        self.assertEqual(experiment.reference_branch.ratio, 2)
        self.assertEqual(
            set(
                experiment.reference_branch.feature_values.all().values_list(
                    "feature_config__id", flat=True
                )
            ),
            {feature_config1.id, feature_config2.id},
        )

        self.assertEqual(len(experiment.treatment_branches), 1)
        self.assertEqual(experiment.treatment_branches[0].name, "new treatment")
        self.assertEqual(experiment.treatment_branches[0].description, "a new treatment")
        self.assertEqual(experiment.treatment_branches[0].ratio, 2)
        self.assertEqual(
            set(
                experiment.treatment_branches[0]
                .feature_values.all()
                .values_list("feature_config__id", flat=True)
            ),
            {feature_config1.id, feature_config2.id},
        )

    def test_serializer_update_branches_with_ids(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config1 = NimbusFeatureConfigFactory.create(application=application)
        feature_config2 = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature_config1, feature_config2],
        )
        branch_ids = set(experiment.branches.all().values_list("id", flat=True))

        reference_branch = {
            "id": experiment.reference_branch.id,
            "name": "new control",
            "description": "a new control",
            "ratio": 2,
            "feature_values": [
                {"feature_config": feature_config1.id, "value": "{}"},
                {"feature_config": feature_config2.id, "value": "{}"},
            ],
        }
        treatment_branch = {
            "id": experiment.treatment_branches[0].id,
            "name": "new treatment",
            "description": "a new treatment",
            "ratio": 2,
            "feature_values": [
                {"feature_config": feature_config1.id, "value": "{}"},
                {"feature_config": feature_config2.id, "value": "{}"},
            ],
        }
        data = {
            "feature_configs": [feature_config1.id, feature_config2.id],
            "reference_branch": reference_branch,
            "treatment_branches": [treatment_branch],
            "changelog_message": "test changelog message",
        }

        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(
            set(experiment.feature_configs.all().values_list("id", flat=True)),
            {feature_config1.id, feature_config2.id},
        )
        self.assertEqual(
            set(experiment.branches.all().values_list("id", flat=True)), branch_ids
        )

        self.assertEqual(experiment.reference_branch.name, "new control")
        self.assertEqual(experiment.reference_branch.description, "a new control")
        self.assertEqual(experiment.reference_branch.ratio, 2)
        self.assertEqual(
            set(
                experiment.reference_branch.feature_values.all().values_list(
                    "feature_config__id", flat=True
                )
            ),
            {feature_config1.id, feature_config2.id},
        )

        self.assertEqual(len(experiment.treatment_branches), 1)
        self.assertEqual(experiment.treatment_branches[0].name, "new treatment")
        self.assertEqual(experiment.treatment_branches[0].description, "a new treatment")
        self.assertEqual(experiment.treatment_branches[0].ratio, 2)
        self.assertEqual(
            set(
                experiment.treatment_branches[0]
                .feature_values.all()
                .values_list("feature_config__id", flat=True)
            ),
            {feature_config1.id, feature_config2.id},
        )
