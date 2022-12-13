from django_test_migrations.contrib.unittest_case import MigratorTestCase

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment as Experiment


class TestMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0221_nimbusexperiment__enrollment_end_date",
    )
    migrate_to = (
        "experiments",
        "0222_analysis_add_basis",
    )

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        user = User.objects.create(email="test@example.com")

        # create experiment without analysis_basis
        NimbusExperiment.objects.create(
            owner=user,
            name="test experiment",
            slug="test-experiment",
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

        # create experiment with analysis_basis
        NimbusExperiment.objects.create(
            owner=user,
            name="another experiment",
            slug="another-experiment",
            application=Experiment.Application.DESKTOP,
            status=NimbusConstants.Status.DRAFT,
            results_data={
                "daily": {"enrollments": {"all": {"control": [], "treatment": []}}},
                "weekly": {"enrollments": {"all": {"control": {}, "treatment": {}}}},
                "overall": {"enrollments": {"all": {"control": {}, "treatment": {}}}},
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

        changed_data = NimbusExperiment.objects.get(slug="test-experiment").results_data

        default_analysis_basis = "enrollments"

        self.assertTrue(default_analysis_basis in changed_data["daily"])
        self.assertFalse("all" in changed_data["daily"])
        self.assertTrue(default_analysis_basis in changed_data["weekly"])
        self.assertFalse("all" in changed_data["weekly"])
        self.assertTrue(default_analysis_basis in changed_data["overall"])
        self.assertFalse("all" in changed_data["overall"])
        self.assertFalse(default_analysis_basis in changed_data["metadata"])

        unchanged_data = NimbusExperiment.objects.get(
            slug="another-experiment"
        ).results_data

        self.assertTrue(default_analysis_basis in unchanged_data["daily"])
        self.assertFalse("all" in unchanged_data["daily"])
        self.assertFalse(default_analysis_basis in unchanged_data["other_metrics"])

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
        self.assertEquals(empty_results_data.results_data, results)
