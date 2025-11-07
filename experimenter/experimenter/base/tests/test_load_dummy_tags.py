from django.core.management import call_command
from django.test import TestCase

from experimenter.experiments.models import Tag


class TestInitialData(TestCase):
    def test_load_dummy_tags(self):
        self.assertFalse(Tag.objects.exists())
        call_command("load_dummy_tags")
        self.assertEqual(Tag.objects.all().count(), 8)
