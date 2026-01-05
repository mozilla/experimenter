from django.test import TestCase

from experimenter.glean.tests.factories import PrefsFactory


class TestPrefs(TestCase):
    def test_str(self):
        prefs1 = PrefsFactory.create(
            alert_dismissed=True, opt_out=True, nimbus_user_id=None
        )
        self.assertEqual(
            f"{prefs1}",
            f"Prefs(user={prefs1.user},alert_dismissed=True,opt_out=True,nimbus_user_id=None)",
        )

        prefs2 = PrefsFactory.create(
            alert_dismissed=True,
            opt_out=False,
            nimbus_user_id="00000000-0000-0000-0000-000000000000",
        )
        self.assertEqual(
            f"{prefs2}",
            (
                f"Prefs(user={prefs2.user},alert_dismissed=True,opt_out=False,"
                "nimbus_user_id=00000000-0000-0000-0000-000000000000)"
            ),
        )

    def test_save_removes_nimbus_user_id(self):
        prefs1 = PrefsFactory.create(
            alert_dismissed=True,
            opt_out=True,
            nimbus_user_id="00000000-0000-0000-0000-000000000000",
        )
        self.assertIsNone(prefs1.nimbus_user_id)

    def test_save_creates_nimbus_user_id(self):
        prefs2 = PrefsFactory.create(
            alert_dismissed=True, opt_out=False, nimbus_user_id=None
        )
        self.assertIsNotNone(prefs2.nimbus_user_id)
