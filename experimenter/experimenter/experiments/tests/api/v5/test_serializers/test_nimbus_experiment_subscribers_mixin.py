from django.contrib.auth.models import User
from django.test import TestCase

from experimenter.experiments.api.v5.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.openidc.tests.factories import UserFactory


class TestNimbusExperimentSubscribersMixin(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_can_update_subscribers_with_existing_subscribers(self):
        subscriber: User = UserFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            subscribers=[subscriber],
        )
        new_subscriber: User = UserFactory.create()

        serializer = NimbusExperimentSerializer(
            experiment,
            {
                "subscribers": [{"email": new_subscriber.email, "subscribed": True}],
                "changelog_message": "Test unsubscribe",
            },
            context={"user": new_subscriber},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        experiment = serializer.save()
        self.assertEqual(list(experiment.subscribers.all()), [subscriber, new_subscriber])

    def test_can_update_subscribers_when_already_subscribed(self):
        subscriber: User = UserFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            subscribers=[subscriber],
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            {
                "subscribers": [{"email": subscriber.email, "subscribed": True}],
                "changelog_message": "Test unsubscribe",
            },
            context={"user": subscriber},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        experiment = serializer.save()
        self.assertEqual(list(experiment.subscribers.all()), [subscriber])

    def test_can_remove_subscribers(self):
        subscriber = UserFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            subscribers=[subscriber],
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            {
                "subscribers": [{"email": subscriber.email, "subscribed": False}],
                "changelog_message": "Test unsubscribe",
            },
            context={"user": subscriber},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        experiment = serializer.save()
        self.assertEqual(list(experiment.subscribers.all()), [])

    def test_can_remove_subscribers_with_no_existing_subscribers(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            subscribers=[],
        )
        new_subscriber = UserFactory.create()

        serializer = NimbusExperimentSerializer(
            experiment,
            {
                "subscribers": [{"email": new_subscriber.email, "subscribed": False}],
                "changelog_message": "Test unsubscribe",
            },
            context={"user": new_subscriber},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        experiment = serializer.save()
        self.assertEqual(list(experiment.subscribers.all()), [])

    def test_can_update_subscribers_with_no_existing_subscribers(self):
        subscriber: User = UserFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            subscribers=[],
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            {
                "subscribers": [{"email": subscriber.email, "subscribed": True}],
                "changelog_message": "Test unsubscribe",
            },
            context={"user": subscriber},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        experiment = serializer.save()
        self.assertEqual(list(experiment.subscribers.all()), [subscriber])
