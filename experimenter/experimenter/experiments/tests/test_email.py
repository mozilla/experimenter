import datetime

from django.core import mail
from django.test import TestCase

from experimenter.experiments.email import (
    nimbus_send_enrollment_ending_email,
    nimbus_send_experiment_ending_email,
)
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.openidc.tests.factories import UserFactory


class TestNimbusEmail(TestCase):
    def test_send_experiment_ending_email(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            start_date=datetime.date.today() - datetime.timedelta(days=10),
            proposed_duration=10,
            subscribers=[],
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

    def test_send_experiment_ending_email_to_subscribers(self):
        subscriber1 = UserFactory.create()
        subscriber2 = UserFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            start_date=datetime.date.today() - datetime.timedelta(days=10),
            proposed_duration=10,
            subscribers=[subscriber1, subscriber2],
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

    def test_send_enrollment_ending_email(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=10,
            subscribers=[],
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

    def test_send_enrollment_ending_email_to_subscribers(self):
        subscriber1 = UserFactory.create()
        subscriber2 = UserFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=10,
            subscribers=[subscriber1, subscriber2],
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
