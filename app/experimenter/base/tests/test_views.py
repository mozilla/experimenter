from django.conf import settings
from django.test import TestCase
from django.urls import reverse


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
