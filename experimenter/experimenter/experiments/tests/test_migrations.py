from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestRemoveVpnApplicationsMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0318_alter_nimbusexperiment_application_and_more",
    )
    migrate_to = (
        "experiments",
        "0319_delete_vpn_features",
    )

    def prepare(self):
        User = self.old_state.apps.get_model("auth", "User")
        NimbusFeatureConfig = self.old_state.apps.get_model(
            "experiments", "NimbusFeatureConfig"
        )
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        NimbusIsolationGroup = self.old_state.apps.get_model(
            "experiments", "NimbusIsolationGroup"
        )

        owner, _ = User.objects.get_or_create(
            username="test@example.com",
            defaults={"email": "test@example.com"},
        )

        NimbusFeatureConfig.objects.get_or_create(
            slug="no-feature-vpn-web",
            defaults={
                "name": "No Feature VPN Web",
                "application": "vpn-web",
            },
        )

        NimbusFeatureConfig.objects.get_or_create(
            slug="no-feature-fenix",
            defaults={
                "name": "No Feature Fenix",
                "application": "fenix",
            },
        )

        NimbusExperiment.objects.get_or_create(
            slug="test-vpn-web",
            defaults={
                "name": "Test VPN Web",
                "application": "vpn-web",
                "owner": owner,
            },
        )

        NimbusExperiment.objects.get_or_create(
            slug="test-fenix",
            defaults={
                "name": "Test Fenix",
                "application": "fenix",
                "owner": owner,
            },
        )

        NimbusIsolationGroup.objects.get_or_create(
            application="vpn-web",
            name="test-group",
            instance=1,
        )

        NimbusIsolationGroup.objects.get_or_create(
            application="fenix",
            name="test-group",
            instance=1,
        )

    def test_migration(self):
        NimbusFeatureConfig = self.new_state.apps.get_model(
            "experiments", "NimbusFeatureConfig"
        )
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        NimbusIsolationGroup = self.new_state.apps.get_model(
            "experiments", "NimbusIsolationGroup"
        )

        self.assertFalse(
            NimbusFeatureConfig.objects.filter(slug="no-feature-vpn-web").exists()
        )

        self.assertTrue(
            NimbusFeatureConfig.objects.filter(slug="no-feature-fenix").exists()
        )

        self.assertFalse(NimbusExperiment.objects.filter(application="vpn-web").exists())

        self.assertTrue(NimbusExperiment.objects.filter(application="fenix").exists())

        self.assertFalse(
            NimbusIsolationGroup.objects.filter(application="vpn-web").exists()
        )

        self.assertTrue(NimbusIsolationGroup.objects.filter(application="fenix").exists())
