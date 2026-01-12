from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestRemoveFocusKlarApplicationsMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0310_fix_preview_states",
    )
    migrate_to = (
        "experiments",
        "0311_alter_nimbusexperiment_application_and_more",
    )

    def prepare(self):
        NimbusFeatureConfig = self.old_state.apps.get_model(
            "experiments", "NimbusFeatureConfig"
        )

        self.assertTrue(
            NimbusFeatureConfig.objects.filter(slug="no-feature-focus-android").exists()
        )
        self.assertTrue(
            NimbusFeatureConfig.objects.filter(slug="no-feature-klar-android").exists()
        )
        self.assertTrue(
            NimbusFeatureConfig.objects.filter(slug="no-feature-focus-ios").exists()
        )
        self.assertTrue(
            NimbusFeatureConfig.objects.filter(slug="no-feature-klar-ios").exists()
        )

    def test_migration(self):
        NimbusFeatureConfig = self.new_state.apps.get_model(
            "experiments", "NimbusFeatureConfig"
        )

        self.assertFalse(
            NimbusFeatureConfig.objects.filter(slug="no-feature-focus-android").exists()
        )
        self.assertFalse(
            NimbusFeatureConfig.objects.filter(slug="no-feature-klar-android").exists()
        )
        self.assertFalse(
            NimbusFeatureConfig.objects.filter(slug="no-feature-focus-ios").exists()
        )
        self.assertFalse(
            NimbusFeatureConfig.objects.filter(slug="no-feature-klar-ios").exists()
        )

        self.assertTrue(
            NimbusFeatureConfig.objects.filter(slug="no-feature-fenix").exists()
        )
