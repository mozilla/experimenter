from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestRemoveStaleMetricHubOutcomesMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0343_alter_nimbusalert_alert_type",
    )
    migrate_to = (
        "experiments",
        "0344_remove_stale_metric_hub_outcomes",
    )

    def prepare(self):
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        owner, _ = User.objects.get_or_create(
            username="test@example.com",
            defaults={"email": "test@example.com"},
        )

        NimbusExperiment.objects.create(
            slug="stale-primary",
            name="Stale primary outcome",
            application="firefox-desktop",
            owner=owner,
            primary_outcomes=["pin-email-and-calendar-tabs-early-day-user"],
            secondary_outcomes=[],
        )
        NimbusExperiment.objects.create(
            slug="stale-secondary",
            name="Stale secondary outcome",
            application="firefox-desktop",
            owner=owner,
            primary_outcomes=["networking"],
            secondary_outcomes=[
                "pin-email-and-calendar-tabs-existing-user",
                "firefox_sync",
                "pin-email-and-calendar-tabs-early-day-user",
                "sidebar",
            ],
        )
        NimbusExperiment.objects.create(
            slug="untouched",
            name="Untouched outcomes",
            application="firefox-desktop",
            owner=owner,
            primary_outcomes=["networking"],
            secondary_outcomes=["firefox_sync"],
        )

    def test_migration(self):
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        stale_primary = NimbusExperiment.objects.get(slug="stale-primary")
        self.assertEqual(stale_primary.primary_outcomes, [])
        self.assertEqual(stale_primary.secondary_outcomes, [])

        stale_secondary = NimbusExperiment.objects.get(slug="stale-secondary")
        self.assertEqual(stale_secondary.primary_outcomes, ["networking"])
        self.assertEqual(stale_secondary.secondary_outcomes, ["firefox_sync", "sidebar"])

        untouched = NimbusExperiment.objects.get(slug="untouched")
        self.assertEqual(untouched.primary_outcomes, ["networking"])
        self.assertEqual(untouched.secondary_outcomes, ["firefox_sync"])
