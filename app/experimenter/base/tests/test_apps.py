from django.test import TestCase
from django.core.management import call_command

from experimenter.base.models import Country, Locale


class TestBaseAppConfig(TestCase):

    def test_post_migrations(self):
        # First mess with the already installed data, so it triggers
        # all code branches in the post migration functions.
        Country.objects.filter(code="SV").delete()
        Country.objects.filter(code="FR").update(name="Frankies")
        # Also, mess with Locales
        Locale.objects.filter(code="sv-SE").delete()
        Locale.objects.filter(code="fr").update(name="Franchism")

        call_command("migrate")

        self.assertTrue(Country.objects.get(code="SV"))
        self.assertEqual(Country.objects.get(code="FR").name, "France")

        self.assertTrue(Locale.objects.get(code="sv-SE"))
        self.assertEqual(Locale.objects.get(code="fr").name, "French")
