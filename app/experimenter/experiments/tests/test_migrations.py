from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestMigration(MigratorTestCase):
    migrate_from = ("experiments", "0210_alter_nimbusexperiment_channel")
    migrate_to = ("experiments", "0211_alter_nimbusexperiment_targeting_config_slug")

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        user = User.objects.create(email="test@example.com")
        NimbusExperiment.objects.create(
            owner=user,
            name="no targeting experiment",
            slug="no_targeting_experiment",
            targeting_config_slug="",
        )
        NimbusExperiment.objects.create(
            owner=user,
            name="some targeting experiment",
            slug="some_targeting_experiment",
            targeting_config_slug="some_targeting",
        )

    def test_migration(self):
        """Run the test itself."""
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        self.assertFalse(
            NimbusExperiment.objects.filter(targeting_config_slug="").exists()
        )
        NimbusExperiment.objects.get(targeting_config_slug="no_targeting")
        NimbusExperiment.objects.get(targeting_config_slug="some_targeting")
