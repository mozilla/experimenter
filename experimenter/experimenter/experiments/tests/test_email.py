import datetime
from unittest.mock import patch

from django.core import mail
from django.test import TestCase

from experimenter.experiments.email import (
    nimbus_send_enrollment_ending_email,
    nimbus_send_experiment_ending_email,
)
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)
from experimenter.openidc.tests.factories import UserFactory


class TestNimbusEmail(TestCase):
    @patch("experimenter.slack.tasks.nimbus_send_slack_notification.delay")
    def test_send_experiment_ending_email(self, mock_slack_task):
        feature_config = NimbusFeatureConfigFactory.create(subscribers=[])
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            start_date=datetime.date.today() - datetime.timedelta(days=10),
            proposed_duration=10,
            subscribers=[],
            feature_configs=[feature_config],
        )

        nimbus_send_experiment_ending_email(experiment)

        sent_email = mail.outbox[-1]

        self.assertEqual(
            sent_email.subject,
            NimbusExperiment.EMAIL_EXPERIMENT_END_SUBJECT,
        )
        self.assertEqual(sent_email.content_subtype, "html")
        self.assertTrue(
            experiment.emails.filter(
                type=NimbusExperiment.EmailType.EXPERIMENT_END
            ).exists()
        )
        self.assertEqual(
            sent_email.recipients(),
            [experiment.owner.email],
        )
        self.assertEqual(sent_email.cc, [])
        self.assertIn(experiment.experiment_url, sent_email.body)

        # Verify Slack notification task was queued
        mock_slack_task.assert_called_once_with(
            experiment_id=experiment.id,
            email_addresses=[experiment.owner.email],
            action_text="is ready to end",
        )

    @patch("experimenter.slack.tasks.nimbus_send_slack_notification.delay")
    def test_send_experiment_ending_email_to_subscribers(self, mock_slack_task):
        subscriber1 = UserFactory.create()
        subscriber2 = UserFactory.create()
        feature_config = NimbusFeatureConfigFactory.create(subscribers=[])
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            start_date=datetime.date.today() - datetime.timedelta(days=10),
            proposed_duration=10,
            subscribers=[subscriber1, subscriber2],
            feature_configs=[feature_config],
        )

        nimbus_send_experiment_ending_email(experiment)

        sent_email = mail.outbox[-1]
        self.assertIn(
            experiment.owner.email,
            sent_email.recipients(),
        )
        self.assertIn(subscriber1.email, sent_email.cc)
        self.assertIn(subscriber2.email, sent_email.cc)
        self.assertEqual(len(sent_email.recipients()), 3)

        # Verify Slack notification task includes all recipients
        mock_slack_task.assert_called_once()
        call_args = mock_slack_task.call_args
        self.assertEqual(
            set(call_args.kwargs["email_addresses"]),
            {experiment.owner.email, subscriber1.email, subscriber2.email},
        )

    @patch("experimenter.slack.tasks.nimbus_send_slack_notification.delay")
    def test_send_enrollment_ending_email(self, mock_slack_task):
        feature_config = NimbusFeatureConfigFactory.create(subscribers=[])
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=10,
            subscribers=[],
            feature_configs=[feature_config],
        )

        nimbus_send_enrollment_ending_email(experiment)

        sent_email = mail.outbox[-1]

        self.assertEqual(
            sent_email.subject,
            NimbusExperiment.EMAIL_ENROLLMENT_END_SUBJECT,
        )
        self.assertEqual(sent_email.content_subtype, "html")
        self.assertTrue(
            experiment.emails.filter(
                type=NimbusExperiment.EmailType.ENROLLMENT_END
            ).exists()
        )
        self.assertEqual(
            sent_email.recipients(),
            [experiment.owner.email],
        )
        self.assertEqual(sent_email.cc, [])
        self.assertIn(experiment.experiment_url, sent_email.body)

        # Verify Slack notification task was queued
        mock_slack_task.assert_called_once_with(
            experiment_id=experiment.id,
            email_addresses=[experiment.owner.email],
            action_text="is ready to end enrollment",
        )

    @patch("experimenter.slack.tasks.nimbus_send_slack_notification.delay")
    def test_send_enrollment_ending_email_to_subscribers(self, mock_slack_task):
        subscriber1 = UserFactory.create()
        subscriber2 = UserFactory.create()
        feature_config = NimbusFeatureConfigFactory.create(subscribers=[])
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=10,
            subscribers=[subscriber1, subscriber2],
            feature_configs=[feature_config],
        )

        nimbus_send_enrollment_ending_email(experiment)

        sent_email = mail.outbox[-1]

        self.assertIn(
            experiment.owner.email,
            sent_email.recipients(),
        )
        self.assertIn(subscriber1.email, sent_email.cc)
        self.assertIn(subscriber2.email, sent_email.cc)
        self.assertEqual(len(sent_email.recipients()), 3)

        # Verify Slack notification task includes all recipients
        mock_slack_task.assert_called_once()
        call_args = mock_slack_task.call_args
        self.assertEqual(
            set(call_args.kwargs["email_addresses"]),
            {experiment.owner.email, subscriber1.email, subscriber2.email},
        )
        self.assertEqual(call_args.kwargs["action_text"], "is ready to end enrollment")

    @patch("experimenter.slack.tasks.nimbus_send_slack_notification.delay")
    def test_send_experiment_ending_email_with_feature_subscribers(self, mock_slack_task):
        feature_subscriber1 = UserFactory.create()
        feature_subscriber2 = UserFactory.create()
        experiment_subscriber = UserFactory.create()
        feature_config = NimbusFeatureConfigFactory.create(
            subscribers=[feature_subscriber1, feature_subscriber2]
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            start_date=datetime.date.today() - datetime.timedelta(days=10),
            proposed_duration=10,
            subscribers=[experiment_subscriber],
            feature_configs=[feature_config],
        )

        nimbus_send_experiment_ending_email(experiment)

        sent_email = mail.outbox[-1]

        self.assertIn(experiment.owner.email, sent_email.recipients())
        self.assertIn(experiment_subscriber.email, sent_email.cc)
        self.assertIn(feature_subscriber1.email, sent_email.cc)
        self.assertIn(feature_subscriber2.email, sent_email.cc)
        self.assertEqual(len(sent_email.cc), 3)

    @patch("experimenter.slack.tasks.nimbus_send_slack_notification.delay")
    def test_send_enrollment_ending_email_with_feature_subscribers(self, mock_slack_task):
        feature_subscriber1 = UserFactory.create()
        feature_subscriber2 = UserFactory.create()
        experiment_subscriber = UserFactory.create()
        feature_config = NimbusFeatureConfigFactory.create(
            subscribers=[feature_subscriber1, feature_subscriber2]
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=10,
            subscribers=[experiment_subscriber],
            feature_configs=[feature_config],
        )

        nimbus_send_enrollment_ending_email(experiment)

        sent_email = mail.outbox[-1]

        self.assertIn(experiment.owner.email, sent_email.recipients())
        self.assertIn(experiment_subscriber.email, sent_email.cc)
        self.assertIn(feature_subscriber1.email, sent_email.cc)
        self.assertIn(feature_subscriber2.email, sent_email.cc)
        self.assertEqual(len(sent_email.cc), 3)

    @patch("experimenter.slack.tasks.nimbus_send_slack_notification.delay")
    def test_send_experiment_ending_email_deduplicates_subscribers(self, mock_slack_task):
        shared_subscriber = UserFactory.create()
        feature_only_subscriber = UserFactory.create()
        experiment_only_subscriber = UserFactory.create()
        feature_config = NimbusFeatureConfigFactory.create(
            subscribers=[shared_subscriber, feature_only_subscriber]
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            start_date=datetime.date.today() - datetime.timedelta(days=10),
            proposed_duration=10,
            subscribers=[shared_subscriber, experiment_only_subscriber],
            feature_configs=[feature_config],
        )

        nimbus_send_experiment_ending_email(experiment)

        sent_email = mail.outbox[-1]

        self.assertIn(experiment.owner.email, sent_email.recipients())
        self.assertEqual(len(sent_email.cc), 3)
        self.assertIn(shared_subscriber.email, sent_email.cc)
        self.assertIn(feature_only_subscriber.email, sent_email.cc)
        self.assertIn(experiment_only_subscriber.email, sent_email.cc)

    @patch("experimenter.slack.tasks.nimbus_send_slack_notification.delay")
    def test_send_experiment_ending_email_feature_subscribers_only(self, mock_slack_task):
        feature_subscriber1 = UserFactory.create()
        feature_subscriber2 = UserFactory.create()
        feature_config = NimbusFeatureConfigFactory.create(
            subscribers=[feature_subscriber1, feature_subscriber2]
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            start_date=datetime.date.today() - datetime.timedelta(days=10),
            proposed_duration=10,
            subscribers=[],
            feature_configs=[feature_config],
        )

        nimbus_send_experiment_ending_email(experiment)

        sent_email = mail.outbox[-1]

        self.assertIn(experiment.owner.email, sent_email.recipients())
        self.assertEqual(len(sent_email.cc), 2)
        self.assertIn(feature_subscriber1.email, sent_email.cc)
        self.assertIn(feature_subscriber2.email, sent_email.cc)

    @patch("experimenter.slack.tasks.nimbus_send_slack_notification.delay")
    def test_send_experiment_ending_email_experiment_subscribers_only(
        self, mock_slack_task
    ):
        experiment_subscriber1 = UserFactory.create()
        experiment_subscriber2 = UserFactory.create()
        feature_config = NimbusFeatureConfigFactory.create(subscribers=[])
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            start_date=datetime.date.today() - datetime.timedelta(days=10),
            proposed_duration=10,
            subscribers=[experiment_subscriber1, experiment_subscriber2],
            feature_configs=[feature_config],
        )

        nimbus_send_experiment_ending_email(experiment)

        sent_email = mail.outbox[-1]

        self.assertIn(experiment.owner.email, sent_email.recipients())
        self.assertEqual(len(sent_email.cc), 2)
        self.assertIn(experiment_subscriber1.email, sent_email.cc)
        self.assertIn(experiment_subscriber2.email, sent_email.cc)
