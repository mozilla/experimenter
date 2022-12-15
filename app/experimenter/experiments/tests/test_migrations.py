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
        "0223_analysis_add_basis",
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
                "v1": {
                    "daily": {"all": {"control": [], "treatment": []}},
                    "weekly": {"all": {"control": {}, "treatment": {}}},
                    "overall": {"all": {"control": {}, "treatment": {}}},
                    "other_metrics": {},
                    "metadata": {},
                    "show_analysis": True,
                    "errors": [],
                }
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
                "v1": {
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

        default_analysis_basis = "enrollments"

        self.assertTrue("v1" in changed_data)
        self.assertTrue("v2" in changed_data)
        # v1 unchanged
        changed_data_v1 = changed_data["v1"]
        self.assertFalse(default_analysis_basis in changed_data_v1["daily"])
        self.assertTrue("all" in changed_data_v1["daily"])
        self.assertFalse(default_analysis_basis in changed_data_v1["weekly"])
        self.assertTrue("all" in changed_data_v1["weekly"])
        self.assertFalse(default_analysis_basis in changed_data_v1["overall"])
        self.assertTrue("all" in changed_data_v1["overall"])
        self.assertFalse(default_analysis_basis in changed_data_v1["metadata"])

        # v2 exists and has analysis basis
        changed_data_v2 = changed_data["v2"]
        self.assertTrue(default_analysis_basis in changed_data_v2["daily"])
        self.assertFalse("all" in changed_data_v2["daily"])
        self.assertTrue(default_analysis_basis in changed_data_v2["weekly"])
        self.assertFalse("all" in changed_data_v2["weekly"])
        self.assertTrue(default_analysis_basis in changed_data_v2["overall"])
        self.assertFalse("all" in changed_data_v2["overall"])
        self.assertFalse(default_analysis_basis in changed_data_v2["metadata"])

        unchanged_data = NimbusExperiment.objects.get(
            slug="another-experiment"
        ).results_data
        self.assertTrue("v1" in unchanged_data)
        self.assertTrue("v2" in unchanged_data)
        # v1 is old schema
        unchanged_data_v1 = unchanged_data["v1"]
        self.assertFalse(default_analysis_basis in unchanged_data_v1["daily"])
        self.assertTrue("all" in unchanged_data_v1["daily"])
        self.assertFalse(default_analysis_basis in unchanged_data_v1["other_metrics"])
        # v2 has analysis basis
        unchanged_data_v2 = unchanged_data["v2"]
        self.assertTrue(default_analysis_basis in unchanged_data_v2["daily"])
        self.assertFalse("all" in unchanged_data_v2["daily"])
        self.assertFalse(default_analysis_basis in unchanged_data_v2["other_metrics"])

        # empty data is still empty
        empty_data = NimbusExperiment.objects.get(slug="empty-experiment").results_data
        self.assertIsNone(empty_data)

        # defined-but-empty schema adds v2 but otherwise remains the same
        empty_results_data = NimbusExperiment.objects.get(
            slug="empty-results-experiment"
        ).results_data

        results = {
            "daily": None,
            "weekly": None,
            "overall": None,
            "metadata": None,
            "show_analysis": True,
        }
        self.assertTrue("v1" in empty_results_data)
        self.assertTrue("v2" in empty_results_data)
        self.assertEquals(empty_results_data["v1"], results)
        self.assertEquals(empty_results_data["v2"], results)
