from django.test import TestCase

from experimenter.base.models import SiteFlag, SiteFlagNameChoices


class TestSiteFlagManager(TestCase):
    def test_value_unset(self):
        self.assertFalse(SiteFlag.objects.value(SiteFlagNameChoices.LAUNCHING_DISABLED))
        self.assertTrue(
            SiteFlag.objects.value(SiteFlagNameChoices.LAUNCHING_DISABLED, True)
        )

    def test_value_set(self):
        SiteFlag(name=SiteFlagNameChoices.LAUNCHING_DISABLED.name, value=True).save()
        self.assertTrue(SiteFlag.objects.value(SiteFlagNameChoices.LAUNCHING_DISABLED))
        self.assertTrue(
            SiteFlag.objects.value(SiteFlagNameChoices.LAUNCHING_DISABLED, False)
        )


class TestSiteFlag(TestCase):
    def test_description_with_choice(self):
        choice = SiteFlagNameChoices.LAUNCHING_DISABLED
        flag = SiteFlag(name=choice.name, value=True)
        self.assertTrue(flag.description, choice.label)

    def test_description_without_choice(self):
        name = "UNKNOWN_FLAG"
        flag = SiteFlag(name=name, value=True)
        self.assertTrue(flag.description, name)

    def test_str(self):
        choice = SiteFlagNameChoices.LAUNCHING_DISABLED
        flag = SiteFlag(name=choice.name, value=True)
        self.assertEqual(f"{flag}", f"{choice.label}: True")
