from datetime import date

from django.conf import settings
from django.core import mail
from django.test import TestCase

from experimenter.legacy.legacy_experiments.constants import ExperimentConstants
from experimenter.legacy.legacy_experiments.email import (
    send_enrollment_pause_email,
    send_experiment_change_email,
    send_experiment_comment_email,
    send_experiment_ending_email,
    send_experiment_launch_email,
    send_intent_to_ship_email,
)
from experimenter.legacy.legacy_experiments.tests.factories import (
    ExperimentChangeLogFactory,
    ExperimentCommentFactory,
    ExperimentFactory,
)
from experimenter.openidc.tests.factories import UserFactory


class TestIntentToShipEmail(TestCase):
    def test_send_intent_to_ship_email_with_risk_fields(self):
        experiment = ExperimentFactory.create(
            name="Experiment",
            slug="experiment",
            risks="Fictitious risk",
            risk_technical_description="Fictitious technical challenge",
            population_percent=10.0,
            firefox_min_version="56.0",
            firefox_max_version="",
            firefox_channel="Nightly",
        )
        sender = "sender@example.com"
        release_drivers = "drivers@example.com"

        user = UserFactory.create(email="smith@example.com")

        experiment.subscribers.add(user)

        with self.settings(EMAIL_SENDER=sender, EMAIL_RELEASE_DRIVERS=release_drivers):
            send_intent_to_ship_email(experiment.id)

        bug_url = settings.BUGZILLA_DETAIL_URL.format(id=experiment.bugzilla_id)
        expected_locales = self.format_locales(experiment)
        expected_countries = self.format_countries(experiment)
        expected_version_channel = self.format_version_and_channel(experiment)

        sent_email = mail.outbox[-1]
        self.assertEqual(
            sent_email.subject, "Delivery Intent to ship: Experiment 56.0 Nightly"
        )
        self.assertEqual(sent_email.from_email, sender)
        self.assertEqual(
            set(sent_email.recipients()),
            set(
                [
                    release_drivers,
                    experiment.owner.email,
                    experiment.analysis_owner,
                    "smith@example.com",
                ]
            ),
        )
        self.assertTrue(
            experiment.emails.filter(
                type=ExperimentConstants.INTENT_TO_SHIP_EMAIL_LABEL
            ).exists()
        )
        self.assertIn(f"Experimenter Bug: {bug_url}", sent_email.body)
        self.assertIn(
            f"Locales: {expected_locales}; {expected_countries}", sent_email.body
        )
        self.assertIn(f"Timeline & Channel: {expected_version_channel}", sent_email.body)
        self.assertIn("Fictitious risk", sent_email.body)
        self.assertIn("Fictitious technical challenge", sent_email.body)

    def test_send_intent_to_ship_email_without_risk_fields(self):
        experiment = ExperimentFactory.create(
            name="Experiment",
            slug="experiment",
            risks="",
            risk_technical_description="",
            population_percent=10.0,
            firefox_min_version="56.0",
            firefox_max_version="",
            firefox_channel="Nightly",
        )

        user = UserFactory.create(email="smith@example.com")

        experiment.subscribers.add(user)
        sender = "sender@example.com"
        release_drivers = "drivers@example.com"

        with self.settings(EMAIL_SENDER=sender, EMAIL_RELEASE_DRIVERS=release_drivers):
            send_intent_to_ship_email(experiment.id)

        bug_url = settings.BUGZILLA_DETAIL_URL.format(id=experiment.bugzilla_id)
        expected_locales = self.format_locales(experiment)
        expected_countries = self.format_countries(experiment)
        expected_version_channel = self.format_version_and_channel(experiment)

        sent_email = mail.outbox[-1]
        self.assertEqual(
            sent_email.subject, "Delivery Intent to ship: Experiment 56.0 Nightly"
        )
        self.assertIn(f"Experimenter Bug: {bug_url}", sent_email.body)
        self.assertIn(
            f"Locales: {expected_locales}; {expected_countries}", sent_email.body
        )
        self.assertIn(f"Timeline & Channel: {expected_version_channel}", sent_email.body)
        self.assertEqual(sent_email.content_subtype, "html")
        self.assertEqual(sent_email.from_email, sender)
        self.assertEqual(
            set(sent_email.recipients()),
            set(
                [
                    release_drivers,
                    experiment.owner.email,
                    experiment.analysis_owner,
                    "smith@example.com",
                ]
            ),
        )

    def format_locales(self, experiment):
        locales = "All locales"
        if experiment.locales.exists():  # pragma: no branch
            locales = ", ".join(str(locale) for locale in experiment.locales.all())
        return locales

    def format_countries(self, experiment):
        countries = "All countries"
        if experiment.countries.exists():  # pragma: no branch
            countries = ", ".join(str(country) for country in experiment.countries.all())
        return countries

    def format_version_and_channel(self, experiment):
        return f"{experiment.format_firefox_versions}" f" {experiment.firefox_channel}"


class TestStatusUpdateEmail(TestCase):
    def setUp(self):
        self.experiment = ExperimentFactory.create_with_variants(
            name="Greatest Experiment",
            slug="greatest-experiment",
            firefox_min_version="68.0",
            firefox_max_version="69.0",
            firefox_channel="Nightly",
            proposed_start_date=date(2019, 5, 1),
            proposed_enrollment=5,
            proposed_duration=10,
        )

        self.experiment.analysis_owner = UserFactory.create()
        self.subscribing_user = UserFactory.create()
        self.experiment.subscribers.add(self.subscribing_user)

    def test_send_experiment_launch_email(self):
        send_experiment_launch_email(self.experiment)

        sent_email = mail.outbox[-1]

        self.assertEqual(
            sent_email.subject,
            "Delivery launched: Greatest Experiment 68.0 to 69.0 Nightly",
        )
        self.assertTrue(
            self.experiment.emails.filter(
                type=ExperimentConstants.EXPERIMENT_STARTS
            ).exists()
        )
        self.assertEqual(sent_email.content_subtype, "html")
        self.assertIn("May 1, 2019", sent_email.body)
        self.assertCountEqual(
            sent_email.recipients(),
            [
                self.experiment.owner.email,
                self.experiment.analysis_owner,
                self.subscribing_user.email,
            ],
        )

        self.assertEqual(self.experiment.emails.count(), 1)

    def test_send_experiment_launch_email_without_analysis_owner(self):
        self.experiment.analysis_owner = None
        self.experiment.save()

        send_experiment_launch_email(self.experiment)

        sent_email = mail.outbox[-1]

        self.assertEqual(
            sent_email.subject,
            "Delivery launched: Greatest Experiment 68.0 to 69.0 Nightly",
        )
        self.assertTrue(
            self.experiment.emails.filter(
                type=ExperimentConstants.EXPERIMENT_STARTS
            ).exists()
        )
        self.assertEqual(sent_email.content_subtype, "html")
        self.assertIn("May 1, 2019", sent_email.body)
        self.assertCountEqual(
            sent_email.recipients(),
            [self.experiment.owner.email, self.subscribing_user.email],
        )

    def test_send_experiment_ending_email(self):
        send_experiment_ending_email(self.experiment)

        sent_email = mail.outbox[-1]

        self.assertEqual(
            sent_email.subject,
            "Delivery ending soon: Greatest Experiment 68.0 to 69.0 Nightly",
        )
        self.assertEqual(sent_email.content_subtype, "html")
        self.assertTrue(
            self.experiment.emails.filter(
                type=ExperimentConstants.EXPERIMENT_ENDS
            ).exists()
        )
        self.assertCountEqual(
            sent_email.recipients(),
            [
                self.experiment.owner.email,
                self.experiment.analysis_owner,
                self.subscribing_user.email,
            ],
        )
        self.assertIn("May 11, 2019", sent_email.body)

    def test_send_experiment_pausing_email(self):
        send_enrollment_pause_email(self.experiment)

        sent_email = mail.outbox[-1]

        self.assertEqual(
            sent_email.subject,
            (
                "Experimenter enrollment ending verification for: "
                "Greatest Experiment 68.0 to 69.0 Nightly"
            ),
        )
        self.assertEqual(sent_email.content_subtype, "html")
        self.assertTrue(
            self.experiment.emails.filter(
                type=ExperimentConstants.EXPERIMENT_PAUSES
            ).exists()
        )
        self.assertCountEqual(
            sent_email.recipients(),
            [
                self.experiment.owner.email,
                self.experiment.analysis_owner,
                self.subscribing_user.email,
            ],
        )
        self.assertIn("May 6, 2019", sent_email.body)

    def test_send_experiment_comment_email(self):
        experiment = ExperimentFactory.create(
            name="exp1", type=ExperimentConstants.TYPE_PREF
        )
        user = UserFactory.create(email="u1@example.com")
        comment = ExperimentCommentFactory.create(experiment=experiment, created_by=user)
        send_experiment_comment_email(comment)
        sent_email = mail.outbox[-1]

        expected_subject = (
            "[Experimenter]: u1@example.com commented on Pref-Flip Experiment: exp1"
        )

        self.assertEqual(sent_email.subject, expected_subject)
        self.assertEqual(sent_email.content_subtype, "html")
        self.assertTrue(
            experiment.emails.filter(type=ExperimentConstants.EXPERIMENT_COMMENT).exists()
        )

    def test_send_experiment_change_email(self):
        experiment = ExperimentFactory.create(
            name="exp1", type=ExperimentConstants.TYPE_PREF
        )
        user = UserFactory.create(email="u1@example.com")
        change = ExperimentChangeLogFactory.create(experiment=experiment, changed_by=user)
        send_experiment_change_email(change)
        sent_email = mail.outbox[-1]

        expected_subject = (
            "[Experimenter]: u1@example.com made a change to Pref-Flip Experiment: exp1"
        )
        self.assertEqual(sent_email.subject, expected_subject)
        self.assertEqual(sent_email.content_subtype, "html")
        self.assertTrue(
            experiment.emails.filter(type=ExperimentConstants.EXPERIMENT_EDIT).exists()
        )
