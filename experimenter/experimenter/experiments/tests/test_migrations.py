from django_test_migrations.contrib.unittest_case import MigratorTestCase

from experimenter.experiments.constants import NimbusConstants


class TestMigrations(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0258_nimbusexperiment_subscribers",
    )
    migrate_to = (
        "experiments",
        "0259_update_proposed_duration",
    )

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        user = User.objects.create(email="test@example.com")

        NimbusExperiment.objects.create(
            owner=user,
            name="test experiment",
            slug="test-experiment",
            application=NimbusConstants.Application.DESKTOP,
            proposed_duration=10,  # Set a value for proposed_duration
            proposed_enrollment=20,  # Set a value for proposed_enrollment
        )

    def test_migration(self):
        """Run the test itself."""
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        experiment = NimbusExperiment.objects.get(slug="test-experiment")
        self.assertEqual(
            experiment.proposed_duration, 20
        )  # Expecting the proposed_duration to be updated
