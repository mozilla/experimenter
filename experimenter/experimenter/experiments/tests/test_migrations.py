from django_test_migrations.contrib.unittest_case import MigratorTestCase

from experimenter.experiments.constants import NimbusConstants


class TestFixPreviewStatesMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0309_nimbusexperiment_enable_review_slack_notifications",
    )
    migrate_to = (
        "experiments",
        "0310_fix_preview_states",
    )

    def prepare(self):
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        owner = User.objects.create(email="test@example.com", username="test")

        NimbusExperiment.objects.create(
            owner=owner,
            name="Experiment with bad state",
            slug="experiment-bad-state",
            application=NimbusConstants.Application.DESKTOP,
            channel=NimbusConstants.Channel.NIGHTLY,
            status=NimbusConstants.Status.PREVIEW,
            status_next=NimbusConstants.Status.PREVIEW,
        )

        NimbusExperiment.objects.create(
            owner=owner,
            name="Experiment with good state",
            slug="experiment-good-state",
            application=NimbusConstants.Application.DESKTOP,
            channel=NimbusConstants.Channel.NIGHTLY,
            status=NimbusConstants.Status.PREVIEW,
            status_next=None,
        )

    def test_migration(self):
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        bad_experiment = NimbusExperiment.objects.get(slug="experiment-bad-state")
        self.assertEqual(bad_experiment.status, NimbusConstants.Status.PREVIEW)
        self.assertIsNone(bad_experiment.status_next)

        good_experiment = NimbusExperiment.objects.get(slug="experiment-good-state")
        self.assertEqual(good_experiment.status, NimbusConstants.Status.PREVIEW)
        self.assertIsNone(good_experiment.status_next)
