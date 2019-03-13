from django.test import TestCase
from django.core.management import call_command

from experimenter.base.models import Country, Locale


class TestInitialData(TestCase):

    def test_load_initial_data(self):
        self.assertTrue(not Country.objects.exists())
        self.assertTrue(not Locale.objects.exists())

        call_command("load-initial-data")

        self.assertTrue(Country.objects.exists())
        self.assertTrue(Locale.objects.exists())

        # First mess with the installed data, so it tests the "corrections"
        # that the managemeent does.
        Country.objects.filter(code="SV").delete()
        Country.objects.filter(code="FR").update(name="Frankies")
        # Also, mess with Locales
        Locale.objects.filter(code="sv-SE").delete()
        Locale.objects.filter(code="fr").update(name="Franchism")

        call_command("load-initial-data")

        self.assertTrue(Country.objects.get(code="SV"))
        self.assertEqual(Country.objects.get(code="FR").name, "France")

        self.assertTrue(Locale.objects.get(code="sv-SE"))
        self.assertEqual(Locale.objects.get(code="fr").name, "French")
