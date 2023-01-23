import datetime

from django.utils import timezone
from django_test_migrations.contrib.unittest_case import MigratorTestCase

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment


class TestMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0224_analysis_add_basis",
    )
    migrate_to = (
        "experiments",
        "0225_nimbusexperiment__updated_date_time",
    )

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        Experiment = self.old_state.apps.get_model("experiments", "NimbusExperiment")
        user = User.objects.create(email="test@example.com")

        ExperimentChangeLog = self.old_state.apps.get_model(
            "experiments", "NimbusChangeLog"
        )

        # create experiment
        experiment = Experiment.objects.create(
            owner=user,
            application=NimbusExperiment.Application.DESKTOP,
            status=NimbusConstants.Status.DRAFT,
            status_next=NimbusConstants.Status.LIVE,
            publish_status=NimbusConstants.PublishStatus.REVIEW,
            name="test experiment",
            slug="test-experiment",
            _start_date=datetime.date.today() - datetime.timedelta(days=3),
        )

        changes = ExperimentChangeLog(
            experiment=experiment,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
            changed_on=timezone.datetime(
                year=2022, month=1, day=2, hour=0, minute=0, second=0
            ),
            changed_by=user,
        )
        changes.save()

    def test_migration(self):
        """Run the test itself."""
        NimbusExperiments = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        experiment = NimbusExperiments.objects.get(slug="test-experiment")
        change = experiment.changes.all().order_by("-changed_on").first()

        self.assertEqual(experiment._updated_date_time, change.changed_on)
