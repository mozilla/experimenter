import requests
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from experimenter.kinto.tests.mixins import MockKintoClientMixin


@override_settings(DEBUG=False)
class TestHeartbeats(MockKintoClientMixin, TestCase):
    def test_heartbeat(self):
        self.mock_kinto_client.server_info.return_value = {
            "user": {"id": "account:experimenter"}
        }
        self.mock_kinto_client.session.request.return_value = {}  # heartbeat

        response = self.client.get("/__heartbeat__")
        self.assertEqual(response.status_code, 200)

    def test_heartbeat_remote_settings_failing(self):
        self.mock_kinto_client.session.request.side_effect = requests.ConnectionError()

        response = self.client.get("/__heartbeat__")
        self.assertTrue(response.status_code >= 500)
        self.assertEqual(response.json()["checks"]["remote_settings_check"], "error")

    def test_heartbeat_remote_settings_bad_auth(self):
        self.mock_kinto_client.server_info.return_value = {}
        self.mock_kinto_client.session.request.return_value = {}  # heartbeat

        response = self.client.get("/__heartbeat__")
        self.assertTrue(response.status_code >= 500)
        self.assertEqual(response.json()["checks"]["remote_settings_check"], "error")

    def test_lbheartbeat(self):
        response = self.client.get("/__lbheartbeat__")
        self.assertEqual(response.status_code, 200)


class TestContextProcessors(TestCase):
    def test_google_analytics_omitted_if_setting_false(self):
        with self.settings(USE_GOOGLE_ANALYTICS=False):
            headers = {settings.OPENIDC_EMAIL_HEADER: "user@example.com"}
            response = self.client.get(reverse("home"), **headers)
            self.assertEqual(response.status_code, 200)
            html = response.content.decode("utf-8")
            # Note the 'not'!
            self.assertNotIn("www.googletagmanager.com", html)

    def test_google_analytics_included_if_setting_true(self):
        with self.settings(USE_GOOGLE_ANALYTICS=True):
            headers = {settings.OPENIDC_EMAIL_HEADER: "user@example.com"}
            response = self.client.get(reverse("home"), **headers)
            self.assertEqual(response.status_code, 200)
            html = response.content.decode("utf-8")
            self.assertIn("www.googletagmanager.com", html)
