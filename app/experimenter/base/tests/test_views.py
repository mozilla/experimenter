from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(DEBUG=False)
class TestHeartbeats(TestCase):
    def test_heartbeat(self):
        response = self.client.get("/__heartbeat__")
        self.assertEqual(response.status_code, 200)

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
