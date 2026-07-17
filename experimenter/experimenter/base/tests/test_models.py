from django.test import TestCase

from experimenter.base.models import SiteFlag, SiteFlagNameChoices


class TestSiteFlagManager(TestCase):
    def test_value_unset(self):
        self.assertFalse(SiteFlag.objects.value(SiteFlagNameChoices.ADVERTISE_DEVTOOLS))
        self.assertTrue(
            SiteFlag.objects.value(SiteFlagNameChoices.ADVERTISE_DEVTOOLS, True)
        )

    def test_value_set(self):
        SiteFlag(name=SiteFlagNameChoices.ADVERTISE_DEVTOOLS.name, value=True).save()
        self.assertTrue(SiteFlag.objects.value(SiteFlagNameChoices.ADVERTISE_DEVTOOLS))
        self.assertTrue(
            SiteFlag.objects.value(SiteFlagNameChoices.ADVERTISE_DEVTOOLS, False)
        )

    def test_caching(self):
        SiteFlag(name=SiteFlagNameChoices.ADVERTISE_DEVTOOLS.name, value=True).save()

        class Request:
            pass

        request = Request()

        with self.assertNumQueries(1):
            site_flag = SiteFlag.objects.get_cached(
                request, SiteFlagNameChoices.ADVERTISE_DEVTOOLS.name
            )

        self.assertTrue(site_flag.value)

        # Caching across the same request does not re-query and returns the same
        # object.
        with self.assertNumQueries(0):
            site_flag_copy = SiteFlag.objects.get_cached(
                request, SiteFlagNameChoices.ADVERTISE_DEVTOOLS.name
            )

        self.assertIs(site_flag, site_flag_copy)

        # SiteFlags are not cached across multiple requests and return different
        # objects.
        request_2 = Request()

        with self.assertNumQueries(1):
            site_flag_2 = SiteFlag.objects.get_cached(
                request_2, SiteFlagNameChoices.ADVERTISE_DEVTOOLS.name
            )

        self.assertIsNot(site_flag_2, site_flag)


class TestSiteFlag(TestCase):
    def test_description_with_choice(self):
        choice = SiteFlagNameChoices.ADVERTISE_DEVTOOLS
        flag = SiteFlag(name=choice.name, value=True)
        self.assertTrue(flag.description, choice.label)

    def test_description_without_choice(self):
        name = "UNKNOWN_FLAG"
        flag = SiteFlag(name=name, value=True)
        self.assertTrue(flag.description, name)

    def test_str(self):
        choice = SiteFlagNameChoices.ADVERTISE_DEVTOOLS
        flag = SiteFlag(name=choice.name, value=True)
        self.assertEqual(f"{flag}", f"{choice.label}: True")
