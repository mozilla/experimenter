from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestMigrations(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0269_nimbusexperiment_conclusion_recommendations",
    )
    migrate_to = (
        "experiments",
        "0270_alter_conclusion_recommendations",
    )

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        owner = User.objects.create()

        # Create NimbusExperiment objects with old values for conclusion_recommendation
        NimbusExperiment.objects.create(
            owner=owner,
            slug="should_change",
            name="should_change",
            conclusion_recommendation="RERUN",
        )

    def test_migration(self):
        """Run the test itself."""
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        self.assertEqual(
            NimbusExperiment.objects.get(slug="should_change").conclusion_recommendations,
            ["RERUN"],
        )
