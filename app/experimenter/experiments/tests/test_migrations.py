from django_test_migrations.contrib.unittest_case import MigratorTestCase

from experimenter.experiments.constants import NimbusConstants


class TestMigration0181Forward(MigratorTestCase):
    migrate_from = ("experiments", "0196_nimbusbranch_feature_enabled")
    migrate_to = ("experiments", "0197_auto_20211109_2000")

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        NimbusIsolationGroup = self.old_state.apps.get_model(
            "experiments", "NimbusIsolationGroup"
        )
        NimbusBucketRange = self.old_state.apps.get_model(
            "experiments", "NimbusBucketRange"
        )

        owner = User.objects.create(email="owner@example.com")

        # An isolation group that was created when an experiment originally launched
        # The associated bucket range will have been deleted when the bucket range
        # was erroneously regenerated
        self.isolation_group = NimbusIsolationGroup.objects.create(
            application=NimbusConstants.Application.FENIX,
            name="fenix-homescreen",
            instance=1,
            total=10000,
        )

        # An experiment with no published_dto and no bucket range
        NimbusExperiment.objects.create(
            owner=owner,
            published_dto=None,
            name="without published_dto",
            slug="without_published_dto",
        )

        # An experiment with no published_dto but with a bucket range
        experiment_with_buckets = NimbusExperiment.objects.create(
            owner=owner,
            published_dto=None,
            name="without published_dto with bucket",
            slug="without_published_dto_with_bucket",
        )
        NimbusBucketRange.objects.create(
            experiment=experiment_with_buckets,
            isolation_group=self.isolation_group,
            start=0,
            count=9000,
        )

        # A launched experiment with a bucket configuration stored at launch
        # in published_dto that doesn't include some new key,
        # in this case the channel
        self.experiment = NimbusExperiment.objects.create(
            owner=owner,
            name="with published_dto",
            slug="with published_dto",
            published_dto={
                "bucketConfig": {
                    "count": 500,
                    "namespace": "fenix-homescreen-1",
                    "randomizationUnit": "nimbus_id",
                    "start": 9000,
                    "total": 10000,
                },
            },
        )

        # An isolation group that was erroneously regenerated
        # at some future time like ending enrolment that now includes a
        # different isolation group name than what was used at launch
        self.isolation_group = NimbusIsolationGroup.objects.create(
            application=NimbusConstants.Application.FENIX,
            name="fenix-homescreen-release",
            instance=1,
            total=10000,
        )

        # A bucket range that that was erroneously regenerated
        # at some future time like ending enrolment that now includes a
        # different start number than what was used at launch
        NimbusBucketRange.objects.create(
            experiment=self.experiment,
            isolation_group=self.isolation_group,
            start=0,
            count=500,
        )

    def test_migration(self):
        """Run the test itself."""
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        experiment = NimbusExperiment.objects.get(id=self.experiment.id)
        self.assertEqual(experiment.bucket_range.isolation_group.name, "fenix-homescreen")
        self.assertEqual(experiment.bucket_range.start, 9000)
