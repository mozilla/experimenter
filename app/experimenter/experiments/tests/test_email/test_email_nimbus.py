import datetime

from django.core import mail
from django.test import TestCase

from experimenter.experiments.email import nimbus_send_experiment_ending_email
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory


class TestNimbusEmail(TestCase):
    def test_send_experiment_ending_email(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            proposed_duration=10,
        )
        experiment.changes.filter(
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
        ).update(changed_on=datetime.datetime.now() - datetime.timedelta(days=10))

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
        self.assertIn(experiment.experiment_url, sent_email.body)
