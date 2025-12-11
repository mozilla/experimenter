import datetime

from django_test_migrations.contrib.unittest_case import MigratorTestCase

from experimenter.experiments.constants import NimbusConstants


class TestDeleteJetstreamChangelogsMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0304_remove_nimbusexperiment_qa_run_type",
    )
    migrate_to = (
        "experiments",
        "0305_delete_jetstream_changelogs",
    )

    def prepare(self):
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        NimbusChangeLog = self.old_state.apps.get_model("experiments", "NimbusChangeLog")

        owner = User.objects.create(email="test@example.com", username="test")

        experiment = NimbusExperiment.objects.create(
            owner=owner,
            name="Test Experiment",
            slug="test-experiment",
            application=NimbusConstants.Application.DESKTOP,
            channel=NimbusConstants.Channel.NIGHTLY,
            status=NimbusConstants.Status.COMPLETE,
        )

        for i in range(5):
            NimbusChangeLog.objects.create(
                experiment=experiment,
                changed_by=owner,
                old_status=NimbusConstants.Status.COMPLETE,
                new_status=NimbusConstants.Status.COMPLETE,
                old_publish_status=NimbusConstants.PublishStatus.IDLE,
                new_publish_status=NimbusConstants.PublishStatus.IDLE,
                message="Experiment results fetched",
                changed_on=datetime.datetime(
                    2024, 1, i + 1, 10, 0, tzinfo=datetime.timezone.utc
                ),
            )

        NimbusChangeLog.objects.create(
            experiment=experiment,
            changed_by=owner,
            old_status=NimbusConstants.Status.DRAFT,
            new_status=NimbusConstants.Status.COMPLETE,
            old_publish_status=NimbusConstants.PublishStatus.IDLE,
            new_publish_status=NimbusConstants.PublishStatus.APPROVED,
            message="Experiment status changed",
            changed_on=datetime.datetime(
                2024, 1, 10, 10, 0, tzinfo=datetime.timezone.utc
            ),
        )

        NimbusChangeLog.objects.create(
            experiment=experiment,
            changed_by=owner,
            old_status=NimbusConstants.Status.COMPLETE,
            new_status=NimbusConstants.Status.COMPLETE,
            old_publish_status=NimbusConstants.PublishStatus.IDLE,
            new_publish_status=NimbusConstants.PublishStatus.IDLE,
            message="Experiment updated",
            changed_on=datetime.datetime(
                2024, 1, 15, 10, 0, tzinfo=datetime.timezone.utc
            ),
        )

    def test_migration(self):
        NimbusChangeLog = self.new_state.apps.get_model("experiments", "NimbusChangeLog")
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        results_fetched_count = NimbusChangeLog.objects.filter(
            message="Experiment results fetched"
        ).count()
        self.assertEqual(results_fetched_count, 0)

        experiment = NimbusExperiment.objects.get(slug="test-experiment")
        remaining_changelogs = NimbusChangeLog.objects.filter(
            experiment=experiment
        ).count()
        self.assertEqual(remaining_changelogs, 2)

        self.assertTrue(
            NimbusChangeLog.objects.filter(message="Experiment status changed").exists()
        )
        self.assertTrue(
            NimbusChangeLog.objects.filter(message="Experiment updated").exists()
        )
