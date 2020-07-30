import random

from django.conf import settings
from django.test import TestCase
from mozilla_nimbus_shared import get_data

from experimenter.experiments.api.v3.serializers import (
    ExperimentRapidSerializer,
    ExperimentRapidStatusSerializer,
)
from experimenter.experiments.models import Experiment, ExperimentChangeLog
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.openidc.tests.factories import UserFactory
from experimenter.base.tests.mixins import MockRequestMixin
from experimenter.bugzilla.tests.mixins import MockBugzillaTasksMixin

NIMBUS_DATA = get_data()
FIREFOX_VERSION = random.choice(Experiment.VERSION_CHOICES)[0]


class TestExperimentRapidSerializer(MockRequestMixin, MockBugzillaTasksMixin, TestCase):
    def test_serializer_outputs_expected_schema_for_draft_experiment(self):
        owner = UserFactory(email="owner@example.com")
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_RAPID,
            rapid_type=Experiment.RAPID_AA_CFR,
            status=Experiment.STATUS_DRAFT,
            owner=owner,
            name="rapid experiment",
            slug="rapid-experiment",
            objectives="gotta go fast",
            audience="all_english",
            features=["picture_in_picture"],
            firefox_min_version=FIREFOX_VERSION,
            firefox_channel=Experiment.CHANNEL_RELEASE,
        )

        serializer = ExperimentRapidSerializer(experiment)

        self.assertDictEqual(
            serializer.data,
            {
                "audience": "all_english",
                "bugzilla_url": "{bug_host}show_bug.cgi?id={bug_id}".format(
                    bug_host=settings.BUGZILLA_HOST, bug_id=experiment.bugzilla_id
                ),
                "features": ["picture_in_picture"],
                "firefox_channel": Experiment.CHANNEL_RELEASE,
                "firefox_min_version": FIREFOX_VERSION,
                "monitoring_dashboard_url": None,
                "name": "rapid experiment",
                "objectives": "gotta go fast",
                "owner": "owner@example.com",
                "slug": "rapid-experiment",
                "status": Experiment.STATUS_DRAFT,
                "reject_feedback": None,
            },
        )

    def test_serializer_outputs_expected_schema_for_live_experiment(self):
        owner = UserFactory(email="owner@example.com")
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_LIVE,
            type=Experiment.TYPE_RAPID,
            rapid_type=Experiment.RAPID_AA_CFR,
            owner=owner,
            name="rapid experiment",
            slug="rapid-experiment",
            objectives="gotta go fast",
            audience="all_english",
            features=["picture_in_picture"],
            firefox_channel=Experiment.CHANNEL_RELEASE,
            firefox_min_version=FIREFOX_VERSION,
            firefox_max_version=None,
        )

        serializer = ExperimentRapidSerializer(experiment)

        self.maxDiff = None
        self.assertDictEqual(
            serializer.data,
            {
                "audience": "all_english",
                "bugzilla_url": "{bug_host}show_bug.cgi?id={bug_id}".format(
                    bug_host=settings.BUGZILLA_HOST, bug_id=experiment.bugzilla_id
                ),
                "features": ["picture_in_picture"],
                "firefox_min_version": FIREFOX_VERSION,
                "firefox_channel": Experiment.CHANNEL_RELEASE,
                "monitoring_dashboard_url": experiment.monitoring_dashboard_url,
                "name": "rapid experiment",
                "objectives": "gotta go fast",
                "owner": "owner@example.com",
                "slug": "rapid-experiment",
                "status": Experiment.STATUS_LIVE,
                "reject_feedback": None,
            },
        )

    def test_serializer_outputs_expected_schema_for_rejected_experiment(self):
        owner = UserFactory(email="owner@example.com")
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_ACCEPTED,
            type=Experiment.TYPE_RAPID,
            rapid_type=Experiment.RAPID_AA_CFR,
            owner=owner,
            name="rapid experiment",
            slug="rapid-experiment",
            objectives="gotta go fast",
            audience="all_english",
            features=["picture_in_picture"],
            firefox_channel=Experiment.CHANNEL_RELEASE,
            firefox_min_version=FIREFOX_VERSION,
            firefox_max_version=None,
        )

        ExperimentChangeLog.objects.create(
            old_status=Experiment.STATUS_ACCEPTED,
            new_status=Experiment.STATUS_REJECTED,
            message="It's no good",
            experiment=experiment,
            changed_by=owner,
            changed_on="2020-07-30T05:37:22.540985Z",
        )

        experiment.status = Experiment.STATUS_REJECTED
        experiment.save()

        serializer = ExperimentRapidSerializer(experiment)

        self.assertDictEqual(
            serializer.data,
            {
                "audience": "all_english",
                "bugzilla_url": "{bug_host}show_bug.cgi?id={bug_id}".format(
                    bug_host=settings.BUGZILLA_HOST, bug_id=experiment.bugzilla_id
                ),
                "features": ["picture_in_picture"],
                "firefox_channel": "Release",
                "firefox_min_version": FIREFOX_VERSION,
                "monitoring_dashboard_url": experiment.monitoring_dashboard_url,
                "name": "rapid experiment",
                "objectives": "gotta go fast",
                "owner": "owner@example.com",
                "slug": "rapid-experiment",
                "status": Experiment.STATUS_REJECTED,
                "reject_feedback": {
                    "changed_on": "2020-07-30T05:37:22.540985Z",
                    "message": "It's no good",
                },
            },
        )

    def test_serializer_required_fields(self):
        serializer = ExperimentRapidSerializer(data={}, context={"request": self.request})
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            set(serializer.errors.keys()),
            set(
                [
                    "name",
                    "objectives",
                    "audience",
                    "features",
                    "firefox_min_version",
                    "firefox_channel",
                ]
            ),
        )

    def test_serializer_bad_audience_value(self):
        data = {
            "name": "rapid experiment",
            "objectives": "gotta go fast",
            "audience": "WRONG AUDIENCE CHOICE",
            "features": ["picture_in_picture", "pinned_tabs"],
            "firefox_min_version": FIREFOX_VERSION,
            "firefox_channel": Experiment.CHANNEL_RELEASE,
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
            "audience": "all_english",
            "features": ["WRONG FEATURE 1", "WRONG FEATURE 2"],
            "firefox_min_version": FIREFOX_VERSION,
            "firefox_channel": Experiment.CHANNEL_RELEASE,
        }
        serializer = ExperimentRapidSerializer(
            data=data, context={"request": self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("features", serializer.errors)

    def test_serializer_bad_firefox_min_version_value(self):
        data = {
            "name": "rapid experiment",
            "objectives": "gotta go fast",
            "audience": "all_english",
            "features": ["picture_in_picture", "pinned_tabs"],
            "firefox_min_version": "invalid version",
            "firefox_channel": Experiment.CHANNEL_RELEASE,
        }
        serializer = ExperimentRapidSerializer(
            data=data, context={"request": self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("firefox_min_version", serializer.errors)

    def test_serializer_bad_firefox_channel_value(self):
        data = {
            "name": "rapid experiment",
            "objectives": "gotta go fast",
            "audience": "all_english",
            "features": ["picture_in_picture", "pinned_tabs"],
            "firefox_min_version": FIREFOX_VERSION,
            "firefox_channel": "invalid channel",
        }
        serializer = ExperimentRapidSerializer(
            data=data, context={"request": self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("firefox_channel", serializer.errors)

    def test_serializer_creates_experiment_and_sets_slug_and_changelog(self):
        data = {
            "name": "rapid experiment",
            "objectives": "gotta go fast",
            "audience": "all_english",
            "features": ["picture_in_picture", "pinned_tabs"],
            "firefox_min_version": FIREFOX_VERSION,
            "firefox_channel": Experiment.CHANNEL_RELEASE,
        }

        serializer = ExperimentRapidSerializer(
            data=data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()

        # User input data
        self.assertEqual(experiment.type, Experiment.TYPE_RAPID)
        self.assertEqual(experiment.rapid_type, Experiment.RAPID_AA_CFR)
        self.assertEqual(experiment.owner, self.user)
        self.assertEqual(experiment.name, "rapid experiment")
        self.assertEqual(experiment.slug, "rapid-experiment")
        self.assertEqual(experiment.objectives, "gotta go fast")
        self.assertEqual(experiment.audience, "all_english")
        self.assertEqual(experiment.features, ["picture_in_picture", "pinned_tabs"])
        self.assertEqual(experiment.firefox_min_version, FIREFOX_VERSION)
        self.assertEqual(experiment.firefox_channel, Experiment.CHANNEL_RELEASE)
        self.assertEqual(
            experiment.public_description, Experiment.BUGZILLA_RAPID_EXPERIMENT_TEMPLATE
        )

        # Preset data
        preset_data = NIMBUS_DATA["ExperimentDesignPresets"]["empty_aa"]["preset"][
            "arguments"
        ]

        self.assertEqual(experiment.firefox_channel, Experiment.CHANNEL_RELEASE)
        self.assertEqual(experiment.proposed_duration, preset_data["proposedDuration"])
        self.assertEqual(
            experiment.proposed_enrollment, preset_data["proposedEnrollment"]
        )

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
                "new_value": "all_english",
                "old_value": None,
            },
            "features": {
                "display_name": "Features",
                "new_value": ["picture_in_picture", "pinned_tabs"],
                "old_value": None,
            },
            "firefox_min_version": {
                "display_name": "Firefox Min Version",
                "new_value": FIREFOX_VERSION,
                "old_value": None,
            },
            "firefox_channel": {
                "display_name": "Firefox Channel",
                "new_value": Experiment.CHANNEL_RELEASE,
                "old_value": None,
            },
            "proposed_duration": {
                "display_name": "Proposed Duration",
                "new_value": 28,
                "old_value": None,
            },
            "proposed_enrollment": {
                "display_name": "Proposed Enrollment",
                "new_value": 7,
                "old_value": None,
            },
        }
        changelog = experiment.changes.get(
            old_status=None, new_status=Experiment.STATUS_DRAFT
        )
        self.maxDiff = None
        self.assertEqual(changelog.changed_values, changed_values)

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
            audience="us_only",
            features=["picture_in_picture", "pinned_tabs"],
            firefox_channel=Experiment.CHANNEL_RELEASE,
            firefox_min_version=FIREFOX_VERSION,
            public_description=Experiment.BUGZILLA_RAPID_EXPERIMENT_TEMPLATE,
        )

        self.assertEqual(experiment.changes.count(), 1)
        data = {
            "name": "changing the name",
            "objectives": "changing objectives",
            "audience": "all_english",
            "features": ["pinned_tabs"],
            "firefox_channel": Experiment.CHANNEL_NIGHTLY,
            "firefox_min_version": Experiment.VERSION_CHOICES[1][0],
        }
        serializer = ExperimentRapidSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()
        self.assertEqual(experiment.changes.count(), 2)

        changed_values = {
            "name": {
                "display_name": "Name",
                "new_value": "changing the name",
                "old_value": "rapid experiment",
            },
            "objectives": {
                "display_name": "Objectives",
                "new_value": "changing objectives",
                "old_value": "gotta go fast",
            },
            "audience": {
                "display_name": "Audience",
                "new_value": "all_english",
                "old_value": "us_only",
            },
            "features": {
                "display_name": "Features",
                "new_value": ["pinned_tabs"],
                "old_value": ["picture_in_picture", "pinned_tabs"],
            },
            "firefox_min_version": {
                "display_name": "Firefox Min Version",
                "new_value": Experiment.VERSION_CHOICES[1][0],
                "old_value": FIREFOX_VERSION,
            },
            "firefox_channel": {
                "display_name": "Firefox Channel",
                "new_value": Experiment.CHANNEL_NIGHTLY,
                "old_value": Experiment.CHANNEL_RELEASE,
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
            "audience": "all_english",
            "features": ["picture_in_picture", "pinned_tabs"],
            "firefox_min_version": FIREFOX_VERSION,
            "firefox_channel": Experiment.CHANNEL_RELEASE,
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
            "audience": "all_english",
            "features": ["picture_in_picture", "pinned_tabs"],
            "firefox_min_version": FIREFOX_VERSION,
            "firefox_channel": Experiment.CHANNEL_RELEASE,
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
            "audience": "all_english",
            "features": ["picture_in_picture", "pinned_tabs"],
            "firefox_min_version": FIREFOX_VERSION,
            "firefox_channel": Experiment.CHANNEL_RELEASE,
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
