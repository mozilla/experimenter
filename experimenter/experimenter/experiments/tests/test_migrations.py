from django_test_migrations.contrib.unittest_case import MigratorTestCase

from experimenter.experiments.constants import NimbusConstants


class TestMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0237_alter_nimbusexperiment_experiment_targeting",
    )
    migrate_to = (
        "experiments",
        "0238_set_draft_published_dto_to_none",
    )

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        user = User.objects.create(email="test@example.com")

        for status in NimbusConstants.Status:
            NimbusExperiment.objects.create(
                owner=user,
                name=f"test experiment {status}",
                slug=f"test-experiment-{status}",
                application=NimbusConstants.Application.DESKTOP,
                status=status,
                publish_status=NimbusConstants.PublishStatus.IDLE,
                published_dto="{}",
            )

    def test_migration(self):
        """Run the test itself."""
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        self.assertEqual(
            set(
                NimbusExperiment.objects.filter(published_dto__isnull=True).values_list(
                    "status", flat=True
                )
            ),
            {NimbusConstants.Status.DRAFT.value},
        )
        self.assertEqual(
            set(
                NimbusExperiment.objects.filter(published_dto="{}").values_list(
                    "status", flat=True
                )
            ),
            {
                NimbusConstants.Status.PREVIEW.value,
                NimbusConstants.Status.LIVE.value,
                NimbusConstants.Status.COMPLETE.value,
            },
        )
