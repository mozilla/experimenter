from django.core.management import call_command
from django.test import TestCase

from experimenter.base.models import SiteFlag, SiteFlagNameChoices


class TestSetSiteFlag(TestCase):
    def test_creates_flag(self):
        call_command("set_site_flag", SiteFlagNameChoices.NEW_DELIVERY_MENU.name, "true")

        self.assertTrue(
            SiteFlag.objects.get(name=SiteFlagNameChoices.NEW_DELIVERY_MENU.name).value
        )

    def test_updates_existing_flag(self):
        SiteFlag.objects.create(
            name=SiteFlagNameChoices.NEW_DELIVERY_MENU.name,
            value=True,
        )

        call_command("set_site_flag", SiteFlagNameChoices.NEW_DELIVERY_MENU.name, "false")

        self.assertFalse(
            SiteFlag.objects.get(name=SiteFlagNameChoices.NEW_DELIVERY_MENU.name).value
        )
