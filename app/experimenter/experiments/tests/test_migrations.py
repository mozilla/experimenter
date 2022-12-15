from django_test_migrations.contrib.unittest_case import MigratorTestCase

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment as Experiment


class TestMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0222_auto_20221207_2104",
    )
    migrate_to = (
        "experiments",
        "0223_analysis_add_schema_version",
    )

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        user = User.objects.create(email="test@example.com")

        # create experiment
        NimbusExperiment.objects.create(
            owner=user,
            name="another experiment",
            slug="another-experiment",
            application=Experiment.Application.DESKTOP,
            status=NimbusConstants.Status.DRAFT,
            results_data={
                "daily": {"all": {"control": [], "treatment": []}},
                "weekly": {"all": {"control": {}, "treatment": {}}},
                "overall": {"all": {"control": {}, "treatment": {}}},
                "other_metrics": {},
                "metadata": {},
                "show_analysis": True,
                "errors": [],
            },
        )

        # create experiment without results_data
        NimbusExperiment.objects.create(
            owner=user,
            name="empty experiment",
            slug="empty-experiment",
            application=Experiment.Application.DESKTOP,
            status=NimbusConstants.Status.DRAFT,
        )

        # create experiment with empty results_data
        NimbusExperiment.objects.create(
            owner=user,
            name="empty results experiment",
            slug="empty-results-experiment",
            application=Experiment.Application.DESKTOP,
            status=NimbusConstants.Status.DRAFT,
            results_data={
                "daily": None,
                "weekly": None,
                "overall": None,
                "metadata": None,
                "show_analysis": True,
            },
        )

    def test_migration(self):
        """Run the test itself."""
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        unchanged_data = NimbusExperiment.objects.get(slug="another-experiment")
        self.assertTrue("v1" in unchanged_data.results_data)
        self.assertFalse("daily" in unchanged_data.results_data)

        empty_data = NimbusExperiment.objects.get(slug="empty-experiment")
        self.assertIsNone(empty_data.results_data)

        empty_results_data = NimbusExperiment.objects.get(slug="empty-results-experiment")
        results = {
            "daily": None,
            "weekly": None,
            "overall": None,
            "metadata": None,
            "show_analysis": True,
        }
        self.assertTrue("v1" in empty_results_data.results_data)
        self.assertEquals(empty_results_data.results_data["v1"], results)
