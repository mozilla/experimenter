from django.test import TestCase

from experimenter.glean.tests.factories import PrefsFactory


class TestPrefsFlag(TestCase):
    def test_str(self):
        prefs = PrefsFactory.create(alert_dismissed=True, opt_out=True)
        self.assertEqual(
            f"{prefs}", f"Prefs(user={prefs.user},alert_dismissed=True,opt_out=True)"
        )
