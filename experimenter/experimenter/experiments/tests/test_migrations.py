from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestMigrations(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0267_alter_nimbusexperiment_application_and_more",
    )
    migrate_to = (
        "experiments",
        "0268_remove_ios_nightly",
    )

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        owner = User.objects.create()

        NimbusExperiment.objects.create(
            owner=owner,
            slug="should_change",
            name="should_change",
            application="ios",
            channel="nightly",
        )

        NimbusExperiment.objects.create(
            owner=owner,
            slug="should_not_change_app",
            name="should_not_change_app",
            application="fenix",
            channel="nightly",
        )
        NimbusExperiment.objects.create(
            owner=owner,
            slug="should_not_change_channel",
            name="should_not_change_channel",
            application="ios",
            channel="beta",
        )

    def test_migration(self):
        """Run the test itself."""
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        self.assertEqual(
            NimbusExperiment.objects.get(slug="should_change").channel, "developer"
        )
        self.assertEqual(
            NimbusExperiment.objects.get(slug="should_not_change_app").channel, "nightly"
        )
        self.assertEqual(
            NimbusExperiment.objects.get(slug="should_not_change_channel").channel, "beta"
        )
