from django.test import TestCase

from experimenter.experiments.api.v3.serializers import ExperimentRapidSerializer
from experimenter.experiments.models import Experiment
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.openidc.tests.factories import UserFactory
from experimenter.experiments.tests.mixins import MockRequestMixin


class TestExperimentRapidSerializer(MockRequestMixin, TestCase):
    def test_serializer_outputs_expected_schema(self):
        owner = UserFactory(email="owner@example.com")
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_RAPID,
            rapid_type=Experiment.RAPID_AA_CFR,
            owner=owner,
            name="rapid experiment",
            slug="rapid-experiment",
            objectives="gotta go fast",
        )

        serializer = ExperimentRapidSerializer(experiment)

        self.assertDictEqual(
            serializer.data,
            {
                "owner": "owner@example.com",
                "name": "rapid experiment",
                "slug": "rapid-experiment",
                "objectives": "gotta go fast",
            },
        )

    def test_serializer_creates_experiment_and_sets_slug(self):
        data = {
            "name": "rapid experiment",
            "objectives": "gotta go fast",
        }

        serializer = ExperimentRapidSerializer(
            data=data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()

        self.assertEqual(experiment.type, Experiment.TYPE_RAPID)
        self.assertEqual(experiment.rapid_type, Experiment.RAPID_AA_CFR)
        self.assertEqual(experiment.owner, self.user)
        self.assertEqual(experiment.name, "rapid experiment")
        self.assertEqual(experiment.slug, "rapid-experiment")
        self.assertEqual(experiment.objectives, "gotta go fast")

    def test_serializer_creates_changelog_with_creations(self):
        data = {
            "name": "this experiment has logs",
            "objectives": "to see whether there are logs",
        }
        serializer = ExperimentRapidSerializer(
            data=data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()
        self.assertEqual(experiment.changes.count(), 1)
        changed_values = {
            "name": {
                "new_value": "this experiment has logs",
                "old_value": None,
                "display_name": "Name",
            },
            "type": {"new_value": "rapid", "old_value": None, "display_name": "Type"},
            "objectives": {
                "new_value": "to see whether there are logs",
                "old_value": None,
                "display_name": "Objectives",
            },
        }
        self.assertTrue(
            experiment.changes.filter(
                old_status=None,
                new_status=Experiment.STATUS_DRAFT,
                changed_values=changed_values,
            ).exists()
        )
