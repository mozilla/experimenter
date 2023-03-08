from django.core.checks import Error
from django.test import TestCase

from experimenter.experiments.constants import NimbusConstants
from experimenter.outcomes import Metric, Outcome, Outcomes, check_outcome_tomls
from experimenter.outcomes.tests import mock_invalid_outcomes, mock_valid_outcomes


@mock_valid_outcomes
class TestOutcomes(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Outcomes.clear_cache()

    def test_load_all_outcomes_and_ignore_examples(self):
        outcomes = Outcomes.all()
        self.assertEqual(len(outcomes), 4)
        self.assertIn(
            Outcome(
                application=NimbusConstants.Application.FENIX,
                description="Fenix config used for testing",
                friendly_name="Fenix config",
                slug="fenix_outcome",
                is_default=False,
                metrics=[
                    Metric(
                        slug="uri_count",
                        friendly_name=None,
                        description=None,
                    )
                ],
            ),
            outcomes,
        )
        for i in range(1, 4):
            self.assertIn(
                Outcome(
                    application=NimbusConstants.Application.DESKTOP,
                    description="Firefox desktop config used for testing",
                    friendly_name=f"Desktop config {i}",
                    slug=f"desktop_outcome_{i}",
                    is_default=False,
                    metrics=[
                        Metric(
                            slug="urlbar_amazon_search_count",
                            friendly_name=None,
                            description=None,
                        ),
                        Metric(
                            slug="total_amazon_search_count",
                            friendly_name=None,
                            description=None,
                        ),
                    ],
                ),
                outcomes,
            )

    def test_load_outcomes_by_application(self):
        desktop_outcomes = Outcomes.by_application(NimbusConstants.Application.DESKTOP)
        self.assertEqual(len(desktop_outcomes), 3)
        for i in range(1, 4):
            self.assertIn(
                Outcome(
                    application=NimbusConstants.Application.DESKTOP,
                    description="Firefox desktop config used for testing",
                    friendly_name=f"Desktop config {i}",
                    slug=f"desktop_outcome_{i}",
                    is_default=False,
                    metrics=[
                        Metric(
                            slug="urlbar_amazon_search_count",
                            friendly_name=None,
                            description=None,
                        ),
                        Metric(
                            slug="total_amazon_search_count",
                            friendly_name=None,
                            description=None,
                        ),
                    ],
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
