from django.conf import settings
from django.test import TestCase
from django.urls import reverse


class TestProjectListView(TestCase):

    def test_list_view_returns_projects(self):
        headers = {
            settings.OPENIDC_EMAIL_HEADER: 'user@example.com',
        }
        response = self.client.get(reverse('projects-list'), **headers)
        self.assertEqual(response.status_code, 200)
