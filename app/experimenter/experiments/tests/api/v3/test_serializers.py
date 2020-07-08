from django.test import TestCase

from experimenter.experiments.api.v3.serializers import (
    ExperimentRapidSerializer,
    ExperimentRapidStatusSerializer,
)
from experimenter.experiments.models import Experiment
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.openidc.tests.factories import UserFactory
from experimenter.base.tests.mixins import MockRequestMixin
from experimenter.bugzilla.tests.mixins import MockBugzillaTasksMixin


class TestExperimentRapidSerializer(MockRequestMixin, MockBugzillaTasksMixin, TestCase):
    def test_serializer_outputs_expected_schema(self):
        owner = UserFactory(email="owner@example.com")
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_RAPID,
            rapid_type=Experiment.RAPID_AA_CFR,
            status=Experiment.STATUS_DRAFT,
            owner=owner,
            name="rapid experiment",
            slug="rapid-experiment",
            objectives="gotta go fast",
            audience="AUDIENCE 1",
            features=["FEATURE 1"],
        )

        serializer = ExperimentRapidSerializer(experiment)

        self.assertDictEqual(
            serializer.data,
            {
                "status": Experiment.STATUS_DRAFT,
                "owner": "owner@example.com",
                "name": "rapid experiment",
                "slug": "rapid-experiment",
                "objectives": "gotta go fast",
                "audience": "AUDIENCE 1",
                "features": ["FEATURE 1"],
            },
        )

    def test_serializer_required_fields(self):
        serializer = ExperimentRapidSerializer(data={}, context={"request": self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)
        self.assertIn("objectives", serializer.errors)
        self.assertIn("audience", serializer.errors)
        self.assertIn("features", serializer.errors)

    def test_serializer_bad_audience_value(self):
        data = {
            "name": "rapid experiment",
            "objectives": "gotta go fast",
            "audience": " WRONG AUDIENCE CHOICE",
            "features": ["FEATURE 1", "FEATURE 2"],
        }
        serializer = ExperimentRapidSerializer(
            data=data, context={"request": self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("audience", serializer.errors)

    def test_serializer_bad_feature_value(self):
        data = {
            "name": "rapid experiment",
            "objectives": "gotta go fast",
            "audience": "AUDIENCE 1",
            "features": ["WRONG FEATURE 1", "WRONG FEATURE 2"],
        }
        serializer = ExperimentRapidSerializer(
            data=data, context={"request": self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("features", serializer.errors)

    def test_serializer_creates_experiment_and_sets_slug_and_changelog(self):

        data = {
            "name": "rapid experiment",
            "objectives": "gotta go fast",
            "audience": "AUDIENCE 1",
            "features": ["FEATURE 1", "FEATURE 2"],
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
        self.assertEqual(
            experiment.public_description, Experiment.BUGZILLA_RAPID_EXPERIMENT_TEMPLATE
        )
        self.assertEqual(experiment.firefox_min_version, Experiment.VERSION_CHOICES[0][0])
        self.assertEqual(experiment.firefox_channel, Experiment.CHANNEL_RELEASE)

        self.mock_tasks_serializer_create_bug.delay.assert_called()

        self.assertEqual(experiment.changes.count(), 1)

        changed_values = {
            "name": {
                "display_name": "Name",
                "new_value": "rapid experiment",
                "old_value": None,
            },
            "objectives": {
                "display_name": "Objectives",
                "new_value": "gotta go fast",
                "old_value": None,
            },
            "owner": {
                "display_name": "Owner",
                "new_value": self.user.id,
                "old_value": None,
            },
            "type": {"display_name": "Type", "new_value": "rapid", "old_value": None},
            "public_description": {
                "display_name": "Public Description",
                "new_value": Experiment.BUGZILLA_RAPID_EXPERIMENT_TEMPLATE,
                "old_value": None,
            },
            "audience": {
                "display_name": "Audience",
                "new_value": "AUDIENCE 1",
                "old_value": None,
            },
            "features": {
                "display_name": "Features",
                "new_value": ["FEATURE 1", "FEATURE 2"],
                "old_value": None,
            },
            "firefox_min_version": {
                "display_name": "Firefox Min Version",
                "new_value": Experiment.VERSION_CHOICES[0][0],
                "old_value": None,
            },
            "firefox_channel": {
                "display_name": "Firefox Channel",
                "new_value": Experiment.CHANNEL_RELEASE,
                "old_value": None,
            },
        }
        self.assertTrue(
            experiment.changes.filter(
                old_status=None,
                new_status=Experiment.STATUS_DRAFT,
                changed_values=changed_values,
            ).exists()
        )

    def test_serializer_creates_changelog_for_updates(self):
        owner = UserFactory(email="owner@example.com")
        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_DRAFT,
            type=Experiment.TYPE_RAPID,
            rapid_type=Experiment.RAPID_AA_CFR,
            owner=owner,
            name="rapid experiment",
            slug="rapid-experiment",
            objectives="gotta go fast",
            audience="AUDIENCE 1",
            features=["FEATURE 1"],
            public_description=Experiment.BUGZILLA_RAPID_EXPERIMENT_TEMPLATE,
        )

        self.assertEqual(experiment.changes.count(), 1)
        data = {
            "name": "changing the name",
            "objectives": "changing objectives",
            "audience": "AUDIENCE 1",
            "features": ["FEATURE 1"],
        }
        serializer = ExperimentRapidSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()
        self.assertEqual(experiment.changes.count(), 2)

        changed_values = {
            "name": {
                "new_value": "changing the name",
                "old_value": "rapid experiment",
                "display_name": "Name",
            },
            "objectives": {
                "new_value": "changing objectives",
                "old_value": "gotta go fast",
                "display_name": "Objectives",
            },
        }
        self.assertTrue(
            experiment.changes.filter(
                old_status=Experiment.STATUS_DRAFT,
                new_status=Experiment.STATUS_DRAFT,
                changed_values=changed_values,
            ).exists()
        )

    def test_serializer_returns_errors_for_non_alpha_numeric_name(self):

        data = {
            "name": "!!!!!!!!!!!!!!!",
            "objectives": "gotta go fast",
            "audience": "AUDIENCE 1",
            "features": ["FEATURE 1", "FEATURE 2"],
        }

        serializer = ExperimentRapidSerializer(
            data=data, context={"request": self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "Name needs to contain alphanumeric characters", serializer.errors["name"]
        )

    def test_serializer_returns_error_for_non_unique_slug(self):

        ExperimentFactory.create(name="non unique slug", slug="non-unique-slug")

        data = {
            "name": "non. unique slug",
            "objectives": "gotta go fast",
            "audience": "AUDIENCE 1",
            "features": ["FEATURE 1", "FEATURE 2"],
        }

        serializer = ExperimentRapidSerializer(
            data=data, context={"request": self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "Name maps to a pre-existing slug, please choose another name",
            serializer.errors["name"],
        )

    def test_serializer_update_experiment_does_not_throw_slug_err(self):

        experiment = ExperimentFactory.create(
            name="non unique slug", slug="non-unique-slug"
        )

        data = {
            "name": "non unique slug",
            "objectives": "gotta go fast",
            "audience": "AUDIENCE 1",
            "features": ["FEATURE 1", "FEATURE 2"],
        }

        serializer = ExperimentRapidSerializer(
            data=data, context={"request": self.request}, instance=experiment
        )
        self.assertTrue(serializer.is_valid())


class TestExperimentRapidStatusSerializer(MockRequestMixin, TestCase):
    def test_serializer_updates_status(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, type=Experiment.TYPE_RAPID
        )

        data = {
            "status": Experiment.STATUS_REVIEW,
        }

        serializer = ExperimentRapidStatusSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(experiment.changes.count(), 1)

        experiment = serializer.save()

        self.assertEqual(experiment.status, Experiment.STATUS_REVIEW)
        self.assertEqual(experiment.changes.count(), 2)

    def test_serializer_rejects_invalid_state_transition(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW, type=Experiment.TYPE_RAPID
        )

        data = {
            "status": Experiment.STATUS_DRAFT,
        }

        serializer = ExperimentRapidStatusSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )

        self.assertFalse(serializer.is_valid())
