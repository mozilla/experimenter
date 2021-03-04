from django.core.checks import Error
from django.test import TestCase

from experimenter.experiments.constants import NimbusConstants
from experimenter.outcomes import Outcome, Outcomes, check_outcome_tomls
from experimenter.outcomes.tests import mock_invalid_outcomes, mock_valid_outcomes


@mock_valid_outcomes
class TestOutcomes(TestCase):
    def setUp(self):
        Outcomes.clear_cache()

    def test_load_all_outcomes_and_ignore_examples(self):
        outcomes = Outcomes.all()
        self.assertEqual(len(outcomes), 4)
        self.assertIn(
            Outcome(
                application=NimbusConstants.Application.FENIX,
                app_name="fenix",
                description="Fenix config used for testing",
                friendly_name="Fenix config",
                slug="fenix_outcome",
            ),
            outcomes,
        )
        for i in range(1, 4):
            self.assertIn(
                Outcome(
                    application=NimbusConstants.Application.DESKTOP,
                    app_name="firefox_desktop",
                    description="Firefox desktop config used for testing",
                    friendly_name=f"Desktop config {i}",
                    slug=f"desktop_outcome_{i}",
                ),
                outcomes,
            )

    def test_load_outcomes_by_app_id(self):
        desktop_outcomes = Outcomes.by_application(NimbusConstants.Application.DESKTOP)
        self.assertEqual(len(desktop_outcomes), 3)
        for i in range(1, 4):
            self.assertIn(
                Outcome(
                    application=NimbusConstants.Application.DESKTOP,
                    app_name="firefox_desktop",
                    description="Firefox desktop config used for testing",
                    friendly_name=f"Desktop config {i}",
                    slug=f"desktop_outcome_{i}",
                ),
                desktop_outcomes,
            )


class TestCheckOutcomeTOMLs(TestCase):
    def setUp(self):
        Outcomes.clear_cache()

    @mock_valid_outcomes
    def test_valid_outcomes_do_not_trigger_check_error(self):
        errors = check_outcome_tomls(None)
        self.assertEqual(errors, [])

    @mock_invalid_outcomes
    def test_invalid_outcomes_do_trigger_check_error(self):
        errors = check_outcome_tomls(None)
        self.assertEqual(
            errors,
            [Error(msg="Error loading Outcome TOMLS 'invalid_app_name'")],
        )
