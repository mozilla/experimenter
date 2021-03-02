import os
import pathlib

from django.core.checks import Error
from django.test import TestCase, override_settings

from experimenter.experiments.constants import NimbusConstants
from experimenter.outcomes import Outcome, Outcomes, check_outcome_tomls


@override_settings(
    JETSTREAM_CONFIG_OUTCOMES_PATH=os.path.join(
        pathlib.Path(__file__).parent.absolute(), "fixtures", "valid_outcomes"
    )
)
class TestOutcomes(TestCase):
    def setUp(self):
        Outcomes.clear_cache()

    def test_load_all_outcomes_and_ignore_examples(self):
        outcomes = Outcomes.all()
        self.assertEqual(len(outcomes), 2)
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
        self.assertIn(
            Outcome(
                application=NimbusConstants.Application.DESKTOP,
                app_name="firefox_desktop",
                description="Firefox desktop config used for testing",
                friendly_name="Desktop config",
                slug="desktop_outcome",
            ),
            outcomes,
        )

    def test_load_outcomes_by_app_id(self):
        desktop_outcomes = Outcomes.by_app_id(NimbusConstants.Application.DESKTOP)
        self.assertEqual(len(desktop_outcomes), 1)
        self.assertIn(
            Outcome(
                application=NimbusConstants.Application.DESKTOP,
                app_name="firefox_desktop",
                description="Firefox desktop config used for testing",
                friendly_name="Desktop config",
                slug="desktop_outcome",
            ),
            desktop_outcomes,
        )


class TestCheckOutcomeTOMLs(TestCase):
    def setUp(self):
        Outcomes.clear_cache()

    @override_settings(
        JETSTREAM_CONFIG_OUTCOMES_PATH=os.path.join(
            pathlib.Path(__file__).parent.absolute(), "fixtures", "valid_outcomes"
        )
    )
    def test_valid_outcomes_do_not_trigger_check_error(self):
        errors = check_outcome_tomls(None)
        self.assertEqual(errors, [])

    @override_settings(
        JETSTREAM_CONFIG_OUTCOMES_PATH=os.path.join(
            pathlib.Path(__file__).parent.absolute(), "fixtures", "invalid_outcomes"
        )
    )
    def test_invalid_outcomes_do_trigger_check_error(self):
        errors = check_outcome_tomls(None)
        self.assertEqual(
            errors,
            [Error(msg="Error loading Outcome TOMLS 'invalid_app_name'")],
        )
