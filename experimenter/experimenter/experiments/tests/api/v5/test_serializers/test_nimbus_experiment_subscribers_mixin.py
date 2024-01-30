from django.test import TestCase
from parameterized import parameterized

from experimenter.experiments.api.v5.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.openidc.tests.factories import UserFactory


class TestNimbusExperimentSubscribersMixin(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    @parameterized.expand([True, False])
    def test_subscribe_and_unsubscribe(self, subscribed):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            subscribers=[],
        )
        current_user = UserFactory.create()
        self.assertFalse(
            current_user.email
            in experiment.subscribers.all().values_list("email", flat=True),
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            {
                "subscribers": [{"email": current_user.email, "subscribed": subscribed}],
                "changelog_message": "Test unsubscribe",
            },
            context={"user": current_user},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        experiment = serializer.save()
        self.assertEqual(current_user in list(experiment.subscribers.all()), subscribed)

    @parameterized.expand([True, False])
    def test_can_update_subscribers_when_already_subscribed(self, subscribed):
        current_user = UserFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            subscribers=[current_user],
        )
        self.assertTrue(
            current_user.email
            in experiment.subscribers.all().values_list("email", flat=True),
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            {
                "subscribers": [{"email": current_user.email, "subscribed": subscribed}],
                "changelog_message": "Test unsubscribe",
            },
            context={"user": current_user},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        experiment = serializer.save()
        self.assertEqual(current_user in list(experiment.subscribers.all()), subscribed)
