from django_test_migrations.contrib.unittest_case import MigratorTestCase

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment


class TestMigrations(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0256_nimbusversionedschema_is_early_startup",
    )
    migrate_to = (
        "experiments",
        "0257_alter_nimbusexperiment_qa_status",
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
            status=NimbusConstants.Status.DRAFT,
            publish_status=NimbusConstants.PublishStatus.IDLE,
            qa_status=None,
        )

    def test_migration(self):
        """Run the test itself."""
        experiment = NimbusExperiment.objects.get(slug="test-experiment")
        self.assertEqual(experiment.qa_status, NimbusConstants.QAStatus.NOT_SET)
