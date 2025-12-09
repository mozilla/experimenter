import datetime

from django_test_migrations.contrib.unittest_case import MigratorTestCase

from experimenter.experiments.constants import NimbusConstants


class TestQARunDateBackfillMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0302_nimbusexperiment_firefox_min_version_parsed",
    )
    migrate_to = (
        "experiments",
        "0303_backfill_qa_run_date_from_changelog",
    )

    def prepare(self):
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        NimbusChangeLog = self.old_state.apps.get_model("experiments", "NimbusChangeLog")

        owner = User.objects.create(email="test@example.com", username="test")

        # Experiment 1: Has QA status changes in changelog but no qa_run_date
        self.experiment1 = NimbusExperiment.objects.create(
            owner=owner,
            name="Experiment with QA status changes",
            slug="experiment-with-qa-changes",
            application=NimbusConstants.Application.DESKTOP,
            channel=NimbusConstants.Channel.NIGHTLY,
            status=NimbusConstants.Status.DRAFT,
            qa_status=NimbusConstants.QAStatus.GREEN,
            qa_run_date=None,
        )

        # Create changelogs showing QA status changes
        NimbusChangeLog.objects.create(
            experiment=self.experiment1,
            changed_by=owner,
            old_status=NimbusConstants.Status.DRAFT,
            new_status=NimbusConstants.Status.DRAFT,
            old_publish_status=NimbusConstants.PublishStatus.IDLE,
            new_publish_status=NimbusConstants.PublishStatus.IDLE,
            experiment_data={"qa_status": NimbusConstants.QAStatus.NOT_SET},
            changed_on=datetime.datetime(2024, 1, 1, 10, 0, tzinfo=datetime.timezone.utc),
        )

        NimbusChangeLog.objects.create(
            experiment=self.experiment1,
            changed_by=owner,
            old_status=NimbusConstants.Status.DRAFT,
            new_status=NimbusConstants.Status.DRAFT,
            old_publish_status=NimbusConstants.PublishStatus.IDLE,
            new_publish_status=NimbusConstants.PublishStatus.IDLE,
            experiment_data={"qa_status": NimbusConstants.QAStatus.YELLOW},
            changed_on=datetime.datetime(
                2024, 1, 15, 14, 30, tzinfo=datetime.timezone.utc
            ),
        )

        self.most_recent_qa_change = datetime.datetime(
            2024, 2, 1, 9, 45, tzinfo=datetime.timezone.utc
        )
        NimbusChangeLog.objects.create(
            experiment=self.experiment1,
            changed_by=owner,
            old_status=NimbusConstants.Status.DRAFT,
            new_status=NimbusConstants.Status.DRAFT,
            old_publish_status=NimbusConstants.PublishStatus.IDLE,
            new_publish_status=NimbusConstants.PublishStatus.IDLE,
            experiment_data={"qa_status": NimbusConstants.QAStatus.GREEN},
            changed_on=self.most_recent_qa_change,
        )

        # Experiment 2: Has qa_run_date already set (should not be modified)
        self.existing_date = datetime.date(2024, 3, 1)
        self.experiment2 = NimbusExperiment.objects.create(
            owner=owner,
            name="Experiment with existing qa_run_date",
            slug="experiment-with-existing-date",
            application=NimbusConstants.Application.DESKTOP,
            channel=NimbusConstants.Channel.BETA,
            status=NimbusConstants.Status.DRAFT,
            qa_status=NimbusConstants.QAStatus.GREEN,
            qa_run_date=self.existing_date,
        )

        # Experiment 3: QA status is NOT_SET (should not be modified)
        self.experiment3 = NimbusExperiment.objects.create(
            owner=owner,
            name="Experiment with NOT_SET QA status",
            slug="experiment-not-set",
            application=NimbusConstants.Application.FENIX,
            channel=NimbusConstants.Channel.NIGHTLY,
            status=NimbusConstants.Status.DRAFT,
            qa_status=NimbusConstants.QAStatus.NOT_SET,
            qa_run_date=None,
        )

        # Experiment 4: Has only one changelog with QA status set
        self.experiment4 = NimbusExperiment.objects.create(
            owner=owner,
            name="Experiment with single changelog",
            slug="experiment-single-changelog",
            application=NimbusConstants.Application.DESKTOP,
            channel=NimbusConstants.Channel.RELEASE,
            status=NimbusConstants.Status.DRAFT,
            qa_status=NimbusConstants.QAStatus.GREEN,
            qa_run_date=None,
        )

        self.single_changelog_date = datetime.datetime(
            2024, 1, 20, 11, 0, tzinfo=datetime.timezone.utc
        )
        NimbusChangeLog.objects.create(
            experiment=self.experiment4,
            changed_by=owner,
            old_status=NimbusConstants.Status.DRAFT,
            new_status=NimbusConstants.Status.DRAFT,
            old_publish_status=NimbusConstants.PublishStatus.IDLE,
            new_publish_status=NimbusConstants.PublishStatus.IDLE,
            experiment_data={"qa_status": NimbusConstants.QAStatus.GREEN},
            changed_on=self.single_changelog_date,
        )

    def test_migration(self):
        """Test the qa_run_date backfill migration."""
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        # Test experiment 1: qa_run_date should be set to most recent QA status change
        experiment1 = NimbusExperiment.objects.get(slug="experiment-with-qa-changes")
        self.assertIsNotNone(experiment1.qa_run_date)
        self.assertEqual(experiment1.qa_run_date, self.most_recent_qa_change.date())

        # Test experiment 2: qa_run_date should remain unchanged
        experiment2 = NimbusExperiment.objects.get(slug="experiment-with-existing-date")
        self.assertEqual(experiment2.qa_run_date, self.existing_date)

        # Test experiment 3: qa_run_date should still be None (QA status is NOT_SET)
        experiment3 = NimbusExperiment.objects.get(slug="experiment-not-set")
        self.assertIsNone(experiment3.qa_run_date)

        # Test experiment 4: qa_run_date should be set from single changelog
        experiment4 = NimbusExperiment.objects.get(slug="experiment-single-changelog")
        self.assertIsNotNone(experiment4.qa_run_date)
        self.assertEqual(experiment4.qa_run_date, self.single_changelog_date.date())
