from django.core.checks import Error, Warning
from django.test import TestCase

from experimenter.base import checks


class TestBaseChecks(TestCase):

    def test_bugzilla_settings_happypath(self):
        errors = checks.check_bugzilla_settings(None)
        self.assertEqual(errors, [])

    def test_bugzilla_settings_errors(self):
        with self.settings(BUGZILLA_CREATE_URL="not a valid URL"):
            errors = checks.check_bugzilla_settings(None)
            expected_errors = [
                Error(
                    "settings.BUGZILLA_CREATE_URL ('not a valid URL') "
                    "is not a valid Buzilla URL",
                    hint="Edit your .env file for 'BUGZILLA_CREATE_URL'",
                    id=checks.ERROR_BUGZILLA_SETTINGS,
                )
            ]
            self.assertEqual(errors, expected_errors)

    def test_bugzilla_settings_warnings(self):
        with self.settings(BUGZILLA_API_KEY=""):
            errors = checks.check_bugzilla_settings(None)
            expected_errors = [
                Warning(
                    "settings.BUGZILLA_API_KEY is not set.",
                    id=checks.WARNING_BUGZILLA_SETTINGS,
                )
            ]
            self.assertEqual(errors, expected_errors)
