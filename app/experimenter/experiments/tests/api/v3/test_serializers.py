from collections import OrderedDict

from django.conf import settings
from django.test import TestCase
from mozilla_nimbus_shared import get_data

from experimenter.experiments.api.v3.serializers import (
    ExperimentRapidSerializer,
    ExperimentRapidStatusSerializer,
    ExperimentRapidVariantSerializer,
)
from experimenter.experiments.models import (
    Experiment,
    ExperimentChangeLog,
)
from experimenter.experiments.tests.factories import (
    ExperimentRapidFactory,
    ExperimentVariantFactory,
)
from experimenter.openidc.tests.factories import UserFactory
from experimenter.base.tests.mixins import MockRequestMixin
from experimenter.bugzilla.tests.mixins import MockBugzillaTasksMixin

NIMBUS_DATA = get_data()


class TestExperimentRapidSerializer(MockRequestMixin, MockBugzillaTasksMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.variants_data = [
            {
                "slug": "control",
                "name": "control",
                "ratio": 50,
                "description": "a variant",
                "is_control": True,
            },
            {
                "slug": "variant",
                "name": "variant",
                "ratio": 50,
                "description": "a variant",
                "is_control": False,
            },
        ]

    def test_serializer_outputs_expected_schema_for_draft_experiment(self):
        owner = UserFactory(email="owner@example.com")
        experiment = ExperimentRapidFactory.create_with_status(
            Experiment.STATUS_DRAFT,
            owner=owner,
            name="rapid experiment",
            slug="rapid-experiment",
            objectives="gotta go fast",
            audience="all_english",
            features=["picture_in_picture"],
        )

        serializer = ExperimentRapidSerializer(experiment)
        serializer_data = serializer.data
        serializer_variants_data = serializer_data.pop("variants")

        self.maxDiff = None
        self.assertDictEqual(
            serializer_data,
            {
                "audience": "all_english",
                "bugzilla_url": None,
                "features": ["picture_in_picture"],
                "firefox_channel": experiment.firefox_channel,
                "firefox_min_version": experiment.firefox_min_version,
                "monitoring_dashboard_url": None,
                "name": "rapid experiment",
                "objectives": "gotta go fast",
                "reject_feedback": None,
                "owner": "owner@example.com",
                "slug": "rapid-experiment",
                "recipe_slug": experiment.recipe_slug,
                "status": Experiment.STATUS_DRAFT,
            },
        )
        for variant in experiment.variants.all():
            variant_data = OrderedDict(
                {
                    "id": variant.id,
                    "description": variant.description,
                    "is_control": variant.is_control,
                    "name": variant.name,
                    "ratio": variant.ratio,
                    "value": variant.value,
                }
            )
            self.assertIn(variant_data, serializer_variants_data)

    def test_serializer_outputs_expected_schema_for_live_experiment(self):
        owner = UserFactory(email="owner@example.com")
        experiment = ExperimentRapidFactory.create_with_status(
            Experiment.STATUS_LIVE,
            owner=owner,
            name="rapid experiment",
            slug="rapid-experiment",
            objectives="gotta go fast",
            audience="all_english",
            features=["picture_in_picture"],
        )

        serializer = ExperimentRapidSerializer(experiment)
        serializer_data = serializer.data
        serializer_variants_data = serializer_data.pop("variants")

        self.maxDiff = None
        self.assertDictEqual(
            serializer_data,
            {
                "audience": "all_english",
                "bugzilla_url": "{bug_host}show_bug.cgi?id={bug_id}".format(
                    bug_host=settings.BUGZILLA_HOST, bug_id=experiment.bugzilla_id
                ),
                "features": ["picture_in_picture"],
                "firefox_min_version": experiment.firefox_min_version,
                "firefox_channel": experiment.firefox_channel,
                "monitoring_dashboard_url": experiment.monitoring_dashboard_url,
                "name": "rapid experiment",
                "objectives": "gotta go fast",
                "owner": "owner@example.com",
                "reject_feedback": None,
                "slug": "rapid-experiment",
                "recipe_slug": experiment.recipe_slug,
                "status": Experiment.STATUS_LIVE,
            },
        )

        for variant in experiment.variants.all():
            variant_data = OrderedDict(
                {
                    "id": variant.id,
                    "description": variant.description,
                    "is_control": variant.is_control,
                    "name": variant.name,
                    "ratio": variant.ratio,
                    "value": variant.value,
                }
            )
            self.assertIn(variant_data, serializer_variants_data)

    def test_serializer_outputs_expected_schema_for_rejected_experiment(self):
        owner = UserFactory(email="owner@example.com")
        experiment = ExperimentRapidFactory.create_with_status(
            Experiment.STATUS_ACCEPTED,
            owner=owner,
            name="rapid experiment",
            slug="rapid-experiment",
            objectives="gotta go fast",
            audience="all_english",
            features=["picture_in_picture"],
        )

        changelog = ExperimentChangeLog.objects.create(
            old_status=Experiment.STATUS_ACCEPTED,
            new_status=Experiment.STATUS_REJECTED,
            message="It's no good",
            experiment=experiment,
            changed_by=owner,
        )

        experiment.status = Experiment.STATUS_REJECTED
        experiment.save()

        serializer = ExperimentRapidSerializer(experiment)

        serializer_data = serializer.data
        serializer_data.pop("variants")

        self.maxDiff = None
        self.assertDictEqual(
            serializer_data,
            {
                "audience": "all_english",
                "bugzilla_url": "{bug_host}show_bug.cgi?id={bug_id}".format(
                    bug_host=settings.BUGZILLA_HOST, bug_id=experiment.bugzilla_id
                ),
                "features": ["picture_in_picture"],
                "firefox_channel": experiment.firefox_channel,
                "firefox_min_version": experiment.firefox_min_version,
                "monitoring_dashboard_url": experiment.monitoring_dashboard_url,
                "name": "rapid experiment",
                "objectives": "gotta go fast",
                "owner": "owner@example.com",
                "reject_feedback": {
                    "changed_on": changelog.changed_on.isoformat().replace("+00:00", "Z"),
                    "message": "It's no good",
                },
                "slug": "rapid-experiment",
                "recipe_slug": experiment.recipe_slug,
                "status": Experiment.STATUS_REJECTED,
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
                    "variants",
                ]
            ),
        )

    def test_serializer_bad_audience_value(self):
        data = {
            "name": "rapid experiment",
            "objectives": "gotta go fast",
            "audience": "WRONG AUDIENCE CHOICE",
            "features": ["picture_in_picture", "pinned_tabs"],
            "firefox_min_version": "80.0",
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
            "firefox_min_version": "80.0",
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
            "firefox_min_version": "80.0",
            "firefox_channel": "invalid channel",
        }
        serializer = ExperimentRapidSerializer(
            data=data, context={"request": self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("firefox_channel", serializer.errors)

    def test_serializer_bad_duplicate_variant_name(self):
        data = {
            "name": "rapid experiment",
            "objectives": "gotta go fast",
            "audience": "all_english",
            "features": ["picture_in_picture", "pinned_tabs"],
            "firefox_min_version": "80.0",
            "firefox_channel": Experiment.CHANNEL_RELEASE,
            "variants": [
                {
                    "name": "duplicate",
                    "ratio": 50,
                    "description": "a variant",
                    "is_control": True,
                },
                {
                    "name": "duplicate",
                    "ratio": 50,
                    "description": "a variant",
                    "is_control": True,
                },
            ],
        }
        serializer = ExperimentRapidSerializer(
            data=data, context={"request": self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("variants", serializer.errors)

    def test_serializer_creates_experiment_and_sets_slug_and_changelog(self):
        data = {
            "name": "rapid experiment",
            "objectives": "gotta go fast",
            "audience": "all_english",
            "features": ["picture_in_picture", "pinned_tabs"],
            "firefox_min_version": "80.0",
            "firefox_channel": Experiment.CHANNEL_RELEASE,
            "variants": self.variants_data,
        }

        serializer = ExperimentRapidSerializer(
            data=data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()

        # Preset data
        preset_data = NIMBUS_DATA["ExperimentDesignPresets"]["empty_aa"]["preset"][
            "arguments"
        ]

        # User input data
        self.assertEqual(experiment.type, Experiment.TYPE_RAPID)
        self.assertEqual(experiment.rapid_type, Experiment.RAPID_AA)
        self.assertEqual(experiment.owner, self.user)
        self.assertEqual(experiment.name, "rapid experiment")
        self.assertEqual(experiment.slug, "rapid-experiment")
        self.assertEqual(experiment.objectives, "gotta go fast")
        self.assertEqual(experiment.audience, "all_english")
        self.assertEqual(experiment.features, ["picture_in_picture", "pinned_tabs"])
        self.assertEqual(experiment.firefox_min_version, "80.0")
        self.assertEqual(experiment.firefox_channel, Experiment.CHANNEL_RELEASE)
        self.assertEqual(
            experiment.public_description, Experiment.BUGZILLA_RAPID_EXPERIMENT_TEMPLATE
        )
        self.assertEqual(experiment.firefox_channel, Experiment.CHANNEL_RELEASE)
        self.assertEqual(experiment.proposed_duration, preset_data["proposedDuration"])
        self.assertEqual(
            experiment.proposed_enrollment, preset_data["proposedEnrollment"]
        )

        self.assertEqual(experiment.variants.count(), 2)
        self.assertTrue(experiment.variants.filter(**self.variants_data[0]).exists())
        self.assertTrue(experiment.variants.filter(**self.variants_data[1]).exists())

        self.mock_tasks_serializer_create_bug.delay.assert_called()

        self.assertEqual(experiment.changes.count(), 1)

        changelog = experiment.changes.get(
            old_status=None, new_status=Experiment.STATUS_DRAFT
        )
        self.assertEqual(changelog.changed_by, self.request.user)
        self.assertEqual(
            set(changelog.changed_values.keys()),
            set(
                [
                    "audience",
                    "features",
                    "firefox_channel",
                    "firefox_min_version",
                    "name",
                    "objectives",
                    "owner",
                    "proposed_duration",
                    "proposed_enrollment",
                    "public_description",
                    "type",
                    "variants",
                ]
            ),
        )

    def test_serializer_updates_experiment_and_creates_changelog(self):
        owner = UserFactory(email="owner@example.com")
        experiment = ExperimentRapidFactory.create_with_status(
            Experiment.STATUS_DRAFT,
            owner=owner,
            name="rapid experiment",
            slug="rapid-experiment",
            objectives="gotta go fast",
            audience="us_only",
            features=["picture_in_picture", "pinned_tabs"],
            firefox_channel=Experiment.CHANNEL_RELEASE,
            firefox_min_version="79.0",
        )
        experiment.variants.all().delete()
        variant = ExperimentVariantFactory.create(experiment=experiment)

        self.assertEqual(experiment.changes.count(), 1)
        data = {
            "name": "changing the name",
            "objectives": "changing objectives",
            "audience": "all_english",
            "features": ["pinned_tabs"],
            "firefox_channel": Experiment.CHANNEL_NIGHTLY,
            "firefox_min_version": "80.0",
            "variants": [
                {
                    "id": variant.id,
                    "name": "something else",
                    "description": "something",
                    "is_control": True,
                    "ratio": 50,
                    "value": "something",
                },
                {
                    "name": "variant1",
                    "description": "variant1 description",
                    "is_control": False,
                    "ratio": 50,
                    "value": "variant value",
                },
            ],
        }

        serializer = ExperimentRapidSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )

        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()
        self.assertEqual(experiment.changes.count(), 2)

        changelog = experiment.changes.latest()
        self.assertEqual(changelog.old_status, Experiment.STATUS_DRAFT)
        self.assertEqual(changelog.new_status, Experiment.STATUS_DRAFT)
        self.assertEqual(
            set(changelog.changed_values.keys()),
            set(
                [
                    "audience",
                    "features",
                    "firefox_channel",
                    "firefox_min_version",
                    "name",
                    "objectives",
                    "public_description",
                    "variants",
                ]
            ),
        )

    def test_serializer_returns_errors_for_non_alpha_numeric_name(self):
        data = {
            "name": "!!!!!!!!!!!!!!!",
            "objectives": "gotta go fast",
            "audience": "all_english",
            "features": ["picture_in_picture", "pinned_tabs"],
            "firefox_min_version": "80.0",
            "firefox_channel": Experiment.CHANNEL_RELEASE,
            "variants": self.variants_data,
        }

        serializer = ExperimentRapidSerializer(
            data=data, context={"request": self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "Name needs to contain alphanumeric characters", serializer.errors["name"]
        )

    def test_serializer_returns_error_for_non_unique_slug(self):
        ExperimentRapidFactory.create(name="non unique slug", slug="non-unique-slug")

        data = {
            "name": "non. unique slug",
            "objectives": "gotta go fast",
            "audience": "all_english",
            "features": ["picture_in_picture", "pinned_tabs"],
            "firefox_min_version": "80.0",
            "firefox_channel": Experiment.CHANNEL_RELEASE,
            "variants": self.variants_data,
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
        experiment = ExperimentRapidFactory.create(
            name="non unique slug", slug="non-unique-slug"
        )

        data = {
            "name": "non unique slug",
            "objectives": "gotta go fast",
            "audience": "all_english",
            "features": ["picture_in_picture", "pinned_tabs"],
            "firefox_min_version": "80.0",
            "firefox_channel": Experiment.CHANNEL_RELEASE,
            "variants": self.variants_data,
        }

        serializer = ExperimentRapidSerializer(
            data=data, context={"request": self.request}, instance=experiment
        )
        self.assertTrue(serializer.is_valid())


class TestExperimentRapidStatusSerializer(MockRequestMixin, TestCase):
    def test_serializer_updates_status(self):
        experiment = ExperimentRapidFactory.create_with_status(Experiment.STATUS_DRAFT)

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
        experiment = ExperimentRapidFactory.create_with_status(
            Experiment.STATUS_REVIEW, type=Experiment.TYPE_RAPID
        )

        data = {
            "status": Experiment.STATUS_DRAFT,
        }

        serializer = ExperimentRapidStatusSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )

        self.assertFalse(serializer.is_valid())


class TestExperimentRapidVariantSerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        variant = ExperimentVariantFactory.create()

        serializer_data = ExperimentRapidVariantSerializer(instance=variant).data
        self.assertDictEqual(
            {
                "id": variant.id,
                "name": variant.name,
                "ratio": variant.ratio,
                "description": variant.description,
                "is_control": variant.is_control,
                "value": variant.value,
            },
            serializer_data,
        )
