from django.core.management import call_command
from django.test import TestCase

from experimenter.projects.models import Project


class TestInitialData(TestCase):
    def test_load_dummy_projects(self):
        self.assertFalse(Project.objects.exists())
        call_command("load_dummy_projects")
        self.assertEqual(Project.objects.all().count(), 3)
