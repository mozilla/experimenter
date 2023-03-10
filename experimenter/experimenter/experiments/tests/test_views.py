from django.conf import settings
from django.test import TestCase
from django.urls import reverse


class TestNimbusUIView(TestCase):
    def test_page_loads(self):
        user_email = "user@example.com"
        response = self.client.get(
            reverse("nimbus-list"),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)


class Test404View(TestCase):
    def test_404(self):
        user_email = "user@example.com"
        response = self.client.get(
            # test path should be a string that doesn't match any existing url patterns
            # or django will attempt to 301 and append a slash before 404ing
            "/invalid/",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertTemplateUsed(response, "nimbus/404.html")
        self.assertEqual(response.status_code, 404)
