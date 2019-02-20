from django.conf import settings
from django.test import TestCase
from django.urls import reverse


class TestContextProcessors(TestCase):

    def test_render_google_analytics_or_not(self):
        headers = {settings.OPENIDC_EMAIL_HEADER: "user@example.com"}
        response = self.client.get(reverse("home"), **headers)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        self.assertTrue("www.googletagmanager.com" in html)

        with self.settings(USE_GOOGLE_ANALYTICS=False):
            response = self.client.get(reverse("home"), **headers)
            self.assertEqual(response.status_code, 200)
            html = response.content.decode("utf-8")
            # Note the 'not'!
            self.assertTrue("www.googletagmanager.com" not in html)
