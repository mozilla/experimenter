from django.test import TestCase

from experimenter.experiments.api.v5.serializers import (
    NimbusBranchUpdateSerializer,
    NimbusExperimentOverviewSerializer,
    NimbusProbeSetUpdateSerializer,
)
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusProbeSetFactory,
)
from experimenter.openidc.tests.factories import UserFactory


class TestCreateNimbusExperimentSerializer(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_serializer_outputs_expected_schema(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.ACCEPTED,
        )

        serializer = NimbusExperimentOverviewSerializer(experiment)
        data = serializer.data

        self.assertDictEqual(
            data,
            {
                "application": experiment.application,
                "hypothesis": experiment.hypothesis,
                "name": experiment.name,
                "public_description": experiment.public_description,
                "slug": experiment.slug,
            },
        )

    def test_saves_new_experiment_with_changelog(self):
        data = {
            "application": NimbusExperiment.Application.DESKTOP,
            "hypothesis": "It does the thing",
            "name": "The Thing",
            "public_description": "Does it do the thing?",
            "slug": "the_thing",
        }

        serializer = NimbusExperimentOverviewSerializer(
            data=data, context={"user": self.user}
        )

        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()
        self.assertEqual(experiment.changes.count(), 1)

    def test_saves_existing_experiment_with_changelog(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT
        )
        self.assertEqual(experiment.changes.count(), 1)

        data = {
            "application": NimbusExperiment.Application.DESKTOP,
            "hypothesis": "It does the thing",
            "name": "The Thing",
            "public_description": "Does it do the thing?",
            "slug": "the_thing",
        }

        serializer = NimbusExperimentOverviewSerializer(
            experiment, data=data, context={"user": self.user}
        )

        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()
        self.assertEqual(experiment.changes.count(), 2)


class TestUpdateNimbusExperimentSerializer(TestCase):
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


class TestNimbusProbeSetUpdateSerializer(TestCase):
    def test_serializer_updates_probe_sets_on_experiment(self):
        user = UserFactory()
        experiment = NimbusExperimentFactory(probe_sets=[])
        probe_sets = [NimbusProbeSetFactory() for i in range(3)]

        serializer = NimbusProbeSetUpdateSerializer(
            experiment,
            {
                "probe_sets": [p.id for p in probe_sets],
            },
            context={"user": user},
        )

        self.assertEqual(experiment.changes.count(), 0)
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()
        self.assertEqual(experiment.changes.count(), 1)

        self.assertEqual(
            set([p.id for p in experiment.probe_sets.all()]),
            set([p.id for p in probe_sets]),
        )
