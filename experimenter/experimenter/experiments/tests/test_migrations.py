from django_test_migrations.contrib.unittest_case import MigratorTestCase

from experimenter.experiments.models import NimbusExperiment as Experiment


class TestMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0225_nimbusexperiment__updated_date_time",
    )
    migrate_to = (
        "experiments",
        "0226_remove_viz_api_v1",
    )

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        user = User.objects.create(email="test@example.com")

        # create experiment with analysis_basis
        NimbusExperiment.objects.create(
            owner=user,
            name="test experiment",
            slug="test-experiment",
            application=Experiment.Application.DESKTOP,
            status=NimbusExperiment.Status.DRAFT,
            results_data={
                "v1": {
                    "daily": {"all": {"control": [], "treatment": []}},
                    "weekly": {"all": {"control": {}, "treatment": {}}},
                    "overall": {"all": {"control": {}, "treatment": {}}},
                    "other_metrics": {},
                    "metadata": {},
                    "show_analysis": True,
                    "errors": [],
                },
                "v2": {
                    "daily": {"enrollments": {"all": {"control": [], "treatment": []}}},
                    "weekly": {"enrollments": {"all": {"control": {}, "treatment": {}}}},
                    "overall": {"enrollments": {"all": {"control": {}, "treatment": {}}}},
                    "other_metrics": {},
                    "metadata": {},
                    "show_analysis": True,
                    "errors": [],
                },
            },
        )

        # create experiment without results_data
        NimbusExperiment.objects.create(
            owner=user,
            name="empty experiment",
            slug="empty-experiment",
            application=Experiment.Application.DESKTOP,
            status=NimbusExperiment.Status.DRAFT,
        )

        # create experiment with empty results_data
        NimbusExperiment.objects.create(
            owner=user,
            name="empty results experiment",
            slug="empty-results-experiment",
            application=Experiment.Application.DESKTOP,
            status=NimbusExperiment.Status.DRAFT,
            results_data={
                "v2": {
                    "daily": None,
                    "weekly": None,
                    "overall": None,
                    "metadata": None,
                    "show_analysis": True,
                },
            },
        )

    def test_migration(self):
        """Run the test itself."""
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        changed_data = NimbusExperiment.objects.get(slug="test-experiment").results_data
        self.assertFalse("v1" in changed_data)
        self.assertTrue("v2" in changed_data)

        empty_data = NimbusExperiment.objects.get(slug="empty-experiment").results_data

        self.assertIsNone(empty_data)

        empty_results_data = NimbusExperiment.objects.get(
            slug="empty-results-experiment"
        ).results_data

        self.assertFalse("v1" in empty_results_data)
        self.assertTrue("v2" in empty_results_data)
