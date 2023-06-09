from django.test import TestCase

from experimenter.base.tests.factories import LocaleFactory
from experimenter.experiments.api.v5.serializers import NimbusExperimentCloneSerializer
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.openidc.tests.factories import UserFactory


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

    def test_invalid_rollout_branch_slug(self):
        parent = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )
        serializer = NimbusExperimentCloneSerializer(
            data={
                "parent_slug": parent.slug,
                "name": "New Experiment",
                "rollout_branch_slug": "BAD SLUG NOPE",
            },
            context={"user": parent.owner},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("rollout_branch_slug", serializer.errors)

    def test_locales_only_clone_for_desktop_application(self):
        desktop_application = NimbusExperiment.Application.DESKTOP
        locale = LocaleFactory.create()

        parent = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            application=desktop_application,
            locales=[locale.id],
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
        self.assertEqual(list(child.locales.all()), [locale])

    def test_locales_not_clone_for_mobile_application(self):
        mobile_application = NimbusExperiment.Application.FENIX
        locale = LocaleFactory.create()

        parent = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            application=mobile_application,
            locales=[locale.id],
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
        self.assertEqual(list(child.locales.all()), [])

    def test_release_date_not_clone_for_mobile_application(self):
        parent = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            application=NimbusExperiment.Application.FENIX,
            proposed_release_date="2023-12-12",
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
        self.assertIsNone(child.proposed_release_date)
        self.assertIsNone(child.release_date)
        self.assertIsNone(child.enrollment_start_date)
