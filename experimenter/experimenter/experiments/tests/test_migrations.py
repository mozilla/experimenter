from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestMigrations(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0271_remove_nimbusexperiment_conclusion_recommendation",
    )
    migrate_to = (
        "experiments",
        "0272_update_conclusion_recommendation_in_changelogs",
    )

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        NimbusChangeLog = self.old_state.apps.get_model("experiments", "NimbusChangeLog")
        owner = User.objects.create(username="testuser")

        experiment = NimbusExperiment.objects.create(
            owner=owner,
            slug="should_change",
            name="should_change",
            conclusion_recommendations=[],
        )

        NimbusChangeLog.objects.create(
            experiment=experiment,
            changed_by=owner,
            experiment_data={"conclusion_recommendation": "RERUN"},
            message="Initial creation",
            changed_on="2023-05-12T17:00:48.454269Z",
        )

    def test_migration(self):
        """Run the test itself."""
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        NimbusChangeLog = self.new_state.apps.get_model("experiments", "NimbusChangeLog")
        experiment = NimbusExperiment.objects.get(slug="should_change")
        changelog = NimbusChangeLog.objects.get(experiment=experiment)
        self.assertEqual(
            changelog.experiment_data.get("conclusion_recommendations"), ["RERUN"]
        )
        self.assertNotIn("conclusion_recommendation", changelog.experiment_data)
