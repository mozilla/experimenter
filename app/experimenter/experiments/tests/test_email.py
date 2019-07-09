from django.test import TestCase
from django.conf import settings
from django.core import mail

from experimenter.experiments.email import (
    send_intent_to_ship_email,
    send_experiment_launch_email,
    send_experiment_ending_email,
)
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.experiments.constants import ExperimentConstants


class TestIntentToShipEmail(TestCase):
    maxDiff = None

    def test_send_intent_to_ship_email_with_risk_fields(self):
        risk_description = "Hardcoded fictitious technical challenge"
        experiment = ExperimentFactory.create(
            name="Experiment",
            slug="experiment",
            risks="Hardcoded fictitious risk",
            risk_technical_description=risk_description,
            population_percent=10.0,
            firefox_min_version="56.0",
            firefox_max_version="",
        )
        send_intent_to_ship_email(experiment.id)

        sent_email = mail.outbox[-1]
        self.verify_subject(experiment, sent_email)

        bug_url = settings.BUGZILLA_DETAIL_URL.format(
            id=experiment.bugzilla_id
        )
        expected_locales = self.format_locales(experiment)
        expected_countries = self.format_countries(experiment)
        expected_version_channel = self.format_version_and_channel(experiment)

        expected_body = (
            f"""
Hello Release Drivers,

This request is coming from information entered in Experimenter.
Please reach out to the person(s) on cc: with any questions, details,
or discussion. They will email an update if any of the key information
changes. Otherwise they will reach out once the study has fully passed
QA for Release Management sign-off.

Experimenter Bug: {bug_url}
Experimenter URL: {experiment.experiment_url}
Study owner: {experiment.owner.email}
Description: {experiment.short_description}
Timeline & Channel: {expected_version_channel}
Intended study dates: {experiment.dates}
Percent of Population: 10%
Platforms: {experiment.platform}
Locales: {expected_locales}; {expected_countries}
QA Status: {experiment.qa_status}
Meta Bug: {experiment.feature_bugzilla_url}
Related links: {experiment.related_work}
Risk: Hardcoded fictitious risk
Technical Complexity: Hardcoded fictitious technical challenge

Thank you!!
""".lstrip()
        )

        self.assertEqual(expected_body, sent_email.body)
        self.assertEqual(sent_email.from_email, settings.EMAIL_SENDER)
        self.assertEqual(
            sent_email.recipients(),
            [settings.EMAIL_RELEASE_DRIVERS, experiment.owner.email],
        )

    def test_send_intent_to_ship_email_without_risk_fields(self):
        experiment = ExperimentFactory.create(
            name="Experiment",
            slug="experiment",
            risks="",
            risk_technical_description="",
            population_percent=10.0,
            firefox_min_version="56.0",
            firefox_max_version="",
        )
        send_intent_to_ship_email(experiment.id)

        sent_email = mail.outbox[-1]
        self.verify_subject(experiment, sent_email)

        bug_url = settings.BUGZILLA_DETAIL_URL.format(
            id=experiment.bugzilla_id
        )
        expected_locales = self.format_locales(experiment)
        expected_countries = self.format_countries(experiment)
        expected_version_channel = self.format_version_and_channel(experiment)

        expected_body = (
            f"""
Hello Release Drivers,

This request is coming from information entered in Experimenter.
Please reach out to the person(s) on cc: with any questions, details,
or discussion. They will email an update if any of the key information
changes. Otherwise they will reach out once the study has fully passed
QA for Release Management sign-off.

Experimenter Bug: {bug_url}
Experimenter URL: {experiment.experiment_url}
Study owner: {experiment.owner.email}
Description: {experiment.short_description}
Timeline & Channel: {expected_version_channel}
Intended study dates: {experiment.dates}
Percent of Population: 10%
Platforms: {experiment.platform}
Locales: {expected_locales}; {expected_countries}
QA Status: {experiment.qa_status}
Meta Bug: {experiment.feature_bugzilla_url}
Related links: {experiment.related_work}

Thank you!!
""".lstrip()
        )

        self.assertEqual(expected_body, sent_email.body)
        self.assertEqual(sent_email.from_email, settings.EMAIL_SENDER)
        self.assertEqual(
            sent_email.recipients(),
            [settings.EMAIL_RELEASE_DRIVERS, experiment.owner.email],
        )

    def format_locales(self, experiment):
        locales = "All locales"
        if experiment.locales.exists():  # pragma: no branch
            locales = ", ".join(
                str(locale) for locale in experiment.locales.all()
            )
        return locales

    def format_countries(self, experiment):
        countries = "All countries"
        if experiment.countries.exists():  # pragma: no branch
            countries = ", ".join(
                str(country) for country in experiment.countries.all()
            )
        return countries

    def format_version_and_channel(self, experiment):
        return (
            f"{experiment.format_firefox_versions}"
            f" {experiment.firefox_channel}"
        )

    def verify_subject(self, experiment, email):
        expected_subject = (
            f"SHIELD Study Intent to ship: Experiment "
            f"{experiment.format_firefox_versions} "
            f"{experiment.firefox_channel}"
        )

        self.assertEqual(email.subject, expected_subject)


class TestStatusUpdateEmail(TestCase):

    def setUp(self):
        self.experiment = ExperimentFactory.create_with_variants(
            name="Greatest Experiment",
            slug="greatest-experiment",
            firefox_min_version="68.0",
            firefox_max_version="69.0",
            firefox_channel="Nightly",
        )

    def test_send_experiment_launch_email(self):
        send_experiment_launch_email(self.experiment)

        sent_email = mail.outbox[-1]
        self.assertEqual(
            sent_email.subject,
            "Experiment launched: Greatest Experiment 68.0 to 69.0 Nightly",
        )

    def test_send_experiment_ending_email(self):
        send_experiment_ending_email(self.experiment)

        sent_email = mail.outbox[-1]
        self.assertEqual(
            sent_email.subject,
            "Experiment ending soon: Greatest Experiment 68.0 to 69.0 Nightly",
        )

        self.assertTrue(
            self.experiment.emails.filter(
                type=ExperimentConstants.EXPERIMENT_ENDS
            ).exists()
        )

        self.assertEqual(sent_email.content_subtype, "html")
