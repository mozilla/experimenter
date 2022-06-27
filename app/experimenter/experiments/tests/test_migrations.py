from django_test_migrations.contrib.unittest_case import MigratorTestCase

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment as Experiment

DESKTOP_STICKY_TARGETING_SLUGS = [
    "first_run",
    "first_run_chrome",
    "first_run_win1903",
    "not_tcp_study_first_run",
    "windows_userchoice_first_run",
    "infrequent_user_uris",
    "infrequent_user_need_pin",
    "infrequent_user_need_default",
    "infrequent_user_need_default_has_pin",
    "infrequent_user_has_default_need_pin",
    "infrequent_windows_user_need_pin",
    "infrequent_win_user_uris",
    "infrequent_user_5_bookmarks",
    "casual_user_uris",
    "casual_user_need_pin",
    "casual_user_need_default",
    "casual_user_need_default_has_pin",
    "casual_user_has_default_need_pin",
    "regular_user_uris",
    "regular_user_need_pin",
    "regular_user_need_default",
    "regular_user_need_default_has_pin",
    "regular_user_has_default_need_pin",
    "regular_user_uses_fxa",
    "core_user_uris",
]

MOBILE_STICKY_TARGETING_SLUGS = [
    "mobile_new_users",
    "mobile_recently_updated_users",
]

NON_STICKY_TARGETING_SLUGS = [
    "core_user_has_default_need_pin",
    "core_user_need_default",
    "core_user_need_default_has_pin",
    "core_user_need_pin",
    "fx95_desktop_users",
    "homepage_google_dot_com",
    "mac_only",
    "no_enterprise_or_last_30d_vpn_use",
    "no_enterprise_or_past_vpn",
    "no_enterprise_users",
    "no_targeting",
    "not_tcp_study",
    "pocket_common",
    "rally_core_addon_user",
    "urlbar_firefox_suggest",
    "windows_userchoice",
]


class TestMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0213_alter_nimbusexperiment_languages_field_for_mobile_client",
    )
    migrate_to = (
        "experiments",
        "0214_migrate_sticky",
    )

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        user = User.objects.create(email="test@example.com")

        # Desktop experiments that will keep the same targeting slug
        # but have is_sticky set to True
        for desktop_sticky_targeting in DESKTOP_STICKY_TARGETING_SLUGS:
            NimbusExperiment.objects.create(
                owner=user,
                name=desktop_sticky_targeting,
                slug=desktop_sticky_targeting,
                application=Experiment.Application.DESKTOP,
                status=NimbusConstants.Status.DRAFT,
                targeting_config_slug=desktop_sticky_targeting,
                is_sticky=False,
            )

        # Targeting slug 'pip_never_used_sticky' will get replaced with 'pip_never_used'
        # and is_sticky set to True
        NimbusExperiment.objects.create(
            owner=user,
            name="pip_never_used_sticky",
            slug="pip_never_used_sticky",
            application=Experiment.Application.DESKTOP,
            status=NimbusConstants.Status.DRAFT,
            targeting_config_slug="pip_never_used_sticky",
            is_sticky=False,
        )

        # Mobile experiments that will keep the same targeting slug
        # but have is_sticky set to True
        for mobile_sticky_targeting in MOBILE_STICKY_TARGETING_SLUGS:
            NimbusExperiment.objects.create(
                owner=user,
                name=mobile_sticky_targeting,
                slug=mobile_sticky_targeting,
                application=Experiment.Application.FOCUS_ANDROID,
                status=NimbusConstants.Status.DRAFT,
                targeting_config_slug=mobile_sticky_targeting,
                is_sticky=False,
            )

        # Desktop experiments that will keep the same targeting slug
        # and keep is_sticky set to False
        for non_sticky_targeting in NON_STICKY_TARGETING_SLUGS:
            NimbusExperiment.objects.create(
                owner=user,
                name=non_sticky_targeting,
                slug=non_sticky_targeting,
                application=Experiment.Application.DESKTOP,
                status=NimbusConstants.Status.DRAFT,
                targeting_config_slug=non_sticky_targeting,
                is_sticky=False,
            )

    def test_migration(self):
        """Run the test itself."""
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        # Desktop experiments that keep the same sticky targeting slug
        # now have is_sticky set to True
        self.assertEqual(
            NimbusExperiment.objects.filter(
                slug__in=DESKTOP_STICKY_TARGETING_SLUGS, is_sticky=True
            ).count(),
            len(DESKTOP_STICKY_TARGETING_SLUGS),
        )
        self.assertEqual(
            NimbusExperiment.objects.filter(
                slug__in=DESKTOP_STICKY_TARGETING_SLUGS, is_sticky=False
            ).count(),
            0,
        )

        # 'pip_never_used_sticky' becomes 'pip_never_used' with is_sticky set to True
        self.assertFalse(
            NimbusExperiment.objects.filter(
                targeting_config_slug="pip_never_used_sticky"
            ).exists()
        )
        self.assertTrue(
            NimbusExperiment.objects.filter(
                targeting_config_slug="pip_never_used", is_sticky=True
            ).exists()
        )

        # Mobile experiments that keep the same sticky targeting slug
        # now have is_sticky set to True
        self.assertEqual(
            NimbusExperiment.objects.filter(
                slug__in=MOBILE_STICKY_TARGETING_SLUGS, is_sticky=True
            ).count(),
            len(MOBILE_STICKY_TARGETING_SLUGS),
        )
        self.assertEqual(
            NimbusExperiment.objects.filter(
                slug__in=MOBILE_STICKY_TARGETING_SLUGS, is_sticky=False
            ).count(),
            0,
        )

        # Desktop experiments that keep the same non-sticky targeting slug
        # still have is_sticky set to False
        self.assertEqual(
            NimbusExperiment.objects.filter(
                slug__in=NON_STICKY_TARGETING_SLUGS, is_sticky=True
            ).count(),
            0,
        )
        self.assertEqual(
            NimbusExperiment.objects.filter(
                slug__in=NON_STICKY_TARGETING_SLUGS, is_sticky=False
            ).count(),
            len(NON_STICKY_TARGETING_SLUGS),
        )
