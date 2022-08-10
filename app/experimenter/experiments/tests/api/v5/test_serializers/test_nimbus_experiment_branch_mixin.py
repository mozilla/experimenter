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
            "feature_enabled": False,
            "feature_value": "",
        }
        treatment_branch = {
            "name": "treatment",
            "description": "a treatment",
            "ratio": 1,
            "feature_enabled": True,
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
        self.assertEqual(experiment.reference_branch.feature_values.get().enabled, False)
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
            experiment.treatment_branches[0].feature_values.get().enabled, True
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
            "feature_enabled": False,
            "feature_value": "",
        }
        treatment_branch = {
            "name": "new treatment",
            "description": "a new treatment",
            "ratio": 1,
            "feature_enabled": True,
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
        self.assertEqual(experiment.reference_branch.feature_values.get().enabled, False)
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
            experiment.treatment_branches[0].feature_values.get().enabled, True
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
            "feature_enabled": False,
            "feature_value": "",
        }
        treatment_branch = {
            "id": experiment.treatment_branches[0].id,
            "name": "new treatment",
            "description": "a new treatment",
            "ratio": 1,
            "feature_enabled": True,
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
        self.assertEqual(experiment.reference_branch.feature_values.get().enabled, False)
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
            experiment.treatment_branches[0].feature_values.get().enabled, True
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
                    for i in data["treatment_branches"]
                ],
            },
        )

    def test_no_treatment_branches_for_rollout(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            feature_configs=[
                NimbusFeatureConfigFactory(
                    application=NimbusExperiment.Application.DESKTOP
                )
            ],
            is_sticky=True,
            targeting_config_slug=NimbusExperiment.TargetingConfig.MAC_ONLY,
        )
        experiment.is_rollout = True
        experiment.save()
        for branch in experiment.treatment_branches:
            branch.delete()

        data = {
            "application": NimbusExperiment.Application.DESKTOP.value,
            "is_sticky": "false",
            "targeting_config_slug": NimbusExperiment.TargetingConfig.MAC_ONLY.value,
            "treatment_branches": [
                {"name": "treatment A", "description": "desc1", "ratio": 1},
                {"name": "treatment B", "description": "desc2", "ratio": 1},
            ],
            "changelog_message": "test changelog message",
            "channel": "",
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(len(serializer.errors), 1)

        error = serializer.errors["treatment_branches"][0].get("name")
        self.assertIsNotNone(error)
        self.assertEqual(error, NimbusConstants.ERROR_SINGLE_BRANCH_FOR_ROLLOUT)

    def test_valid_branches_for_rollout(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_108,
            is_sticky=True,
            is_rollout=True,
            targeting_config_slug=NimbusExperiment.TargetingConfig.MAC_ONLY,
        )
        experiment.save()
        for branch in experiment.treatment_branches:
            branch.delete()
        data = {
            "application": NimbusExperiment.Application.DESKTOP.value,
            "is_sticky": "true",
            "is_rollout": "true",
            "targeting_config_slug": NimbusExperiment.TargetingConfig.MAC_ONLY.value,
            "firefox_min_version": NimbusExperiment.Version.FIREFOX_108.value,
            "changelog_message": "test changelog message",
            "channel": "",
        }
        serializer = NimbusExperimentSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )

        self.assertTrue(serializer.is_valid())


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
                {"feature_config": feature_config1.id, "enabled": True, "value": "{}"},
                {"feature_config": feature_config2.id, "enabled": True, "value": "{}"},
            ],
        }
        treatment_branch = {
            "name": "treatment",
            "description": "a treatment",
            "ratio": 1,
            "feature_values": [
                {"feature_config": feature_config1.id, "enabled": True, "value": "{}"},
                {"feature_config": feature_config2.id, "enabled": True, "value": "{}"},
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
            set([feature_config1.id, feature_config2.id]),
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
            set([feature_config1.id, feature_config2.id]),
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
            set([feature_config1.id, feature_config2.id]),
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
                {"feature_config": feature_config1.id, "enabled": True, "value": "{}"},
                {"feature_config": feature_config2.id, "enabled": True, "value": "{}"},
            ],
        }
        treatment_branch = {
            "name": "new treatment",
            "description": "a new treatment",
            "ratio": 2,
            "feature_values": [
                {"feature_config": feature_config1.id, "enabled": True, "value": "{}"},
                {"feature_config": feature_config2.id, "enabled": True, "value": "{}"},
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
            set([feature_config1.id, feature_config2.id]),
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
            set([feature_config1.id, feature_config2.id]),
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
            set([feature_config1.id, feature_config2.id]),
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
                {"feature_config": feature_config1.id, "enabled": True, "value": "{}"},
                {"feature_config": feature_config2.id, "enabled": True, "value": "{}"},
            ],
        }
        treatment_branch = {
            "id": experiment.treatment_branches[0].id,
            "name": "new treatment",
            "description": "a new treatment",
            "ratio": 2,
            "feature_values": [
                {"feature_config": feature_config1.id, "enabled": True, "value": "{}"},
                {"feature_config": feature_config2.id, "enabled": True, "value": "{}"},
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
            set([feature_config1.id, feature_config2.id]),
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
            set([feature_config1.id, feature_config2.id]),
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
            set([feature_config1.id, feature_config2.id]),
        )
