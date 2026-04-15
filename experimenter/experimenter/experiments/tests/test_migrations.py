from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestClearMonitoringDataMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0326_alter_nimbusexperiment_next_steps_and_more",
    )
    migrate_to = (
        "experiments",
        "0327_clear_monitoring_data_non_live_complete",
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

        self.monitoring_data = {"total_enrollments": 100, "total_unenrollments": 5}

        for status in ("Draft", "Preview", "Live", "Complete"):
            NimbusExperiment.objects.create(
                slug=f"test-{status.lower()}",
                name=f"Test {status}",
                application="firefox-desktop",
                owner=owner,
                status=status,
                monitoring_data=self.monitoring_data,
            )

    def test_migration(self):
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        self.assertIsNone(NimbusExperiment.objects.get(slug="test-draft").monitoring_data)
        self.assertIsNone(
            NimbusExperiment.objects.get(slug="test-preview").monitoring_data
        )
        self.assertEqual(
            NimbusExperiment.objects.get(slug="test-live").monitoring_data,
            self.monitoring_data,
        )
        self.assertEqual(
            NimbusExperiment.objects.get(slug="test-complete").monitoring_data,
            self.monitoring_data,
        )
