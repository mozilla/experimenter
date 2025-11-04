from unittest import mock

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from experimenter.glean.models import Prefs
from experimenter.glean.tests.factories import PrefsFactory
from experimenter.glean.views import OptOutView
from experimenter.openidc.tests.factories import UserFactory


class GleanAlertDismissedViewTest(TestCase):
    def test_alert_dismissed(self):
        user = UserFactory.create()
        response = self.client.post(
            reverse("glean-alert-dismissed"),
            data={"alert_dismissed": True},
            **{settings.OPENIDC_EMAIL_HEADER: user.email},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Prefs.objects.get(user=user).alert_dismissed)

    def test_alert_dismissed_after_opt_out(self):
        prefs = PrefsFactory.create(opt_out=True)
        response = self.client.post(
            reverse("glean-alert-dismissed"),
            data={"alert_dismissed": True},
            **{settings.OPENIDC_EMAIL_HEADER: prefs.user.email},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Prefs.objects.get(user=prefs.user).alert_dismissed)


class GleanOptOutViewTest(TestCase):
    def test_opt_in(self):
        prefs = PrefsFactory.create(opt_out=True)
        response = self.client.post(
            reverse("glean-opt-out"),
            data={"opt_out": ""},
            **{settings.OPENIDC_EMAIL_HEADER: prefs.user.email},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Prefs.objects.get(user=prefs.user).opt_out)

    def test_opt_out(self):
        user = UserFactory.create()
        with mock.patch.object(
            OptOutView.data_collection_opt_out_ping, "record"
        ) as record:
            response = self.client.post(
                reverse("glean-opt-out"),
                data={"opt_out": "true"},
                **{settings.OPENIDC_EMAIL_HEADER: user.email},
            )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Prefs.objects.get(user=user).opt_out)
        self.assertEqual(
            record.mock_calls,
            [
                mock.call(
                    user_agent=None,
                    ip_address="127.0.0.1",
                    nimbus_nimbus_user_id=str(user.id),
                    events=[],
                )
            ],
        )

    def test_opt_out_after_alert_dismissed(self):
        prefs = PrefsFactory.create(alert_dismissed=True)
        with mock.patch.object(
            OptOutView.data_collection_opt_out_ping, "record"
        ) as record:
            response = self.client.post(
                reverse("glean-opt-out"),
                data={"opt_out": "true"},
                **{settings.OPENIDC_EMAIL_HEADER: prefs.user.email},
            )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Prefs.objects.get(user=prefs.user).opt_out)
        self.assertEqual(
            record.mock_calls,
            [
                mock.call(
                    user_agent=None,
                    ip_address="127.0.0.1",
                    nimbus_nimbus_user_id=str(prefs.user.id),
                    events=[],
                )
            ],
        )
