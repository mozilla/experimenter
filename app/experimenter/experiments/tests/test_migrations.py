from django_test_migrations.contrib.unittest_case import MigratorTestCase

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment as Experiment


class TestMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0217_auto_20220901_1914",
    )
    migrate_to = (
        "experiments",
        "0218_update_results_data_schema",
    )

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        user = User.objects.create(email="test@example.com")

        # create experiment without segments
        NimbusExperiment.objects.create(
            owner=user,
            name="test experiment",
            slug="test-experiment",
            application=Experiment.Application.DESKTOP,
            status=NimbusConstants.Status.DRAFT,
            results_data={
                "daily": {"control": [], "treatment": []},
                "weekly": {"control": {}, "treatment": {}},
                "overall": {"control": {}, "treatment": {}},
                "other_metrics": {},
                "metadata": {},
                "show_analysis": True,
                "errors": [],
            },
        )

        # create experiment with segments
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

    def test_migration(self):
        """Run the test itself."""
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        changed_data = NimbusExperiment.objects.get(slug="test-experiment").results_data

        self.assertTrue("all" in changed_data["daily"])
        self.assertFalse("control" in changed_data["daily"])
        self.assertTrue("all" in changed_data["weekly"])
        self.assertFalse("control" in changed_data["weekly"])
        self.assertTrue("all" in changed_data["overall"])
        self.assertFalse("control" in changed_data["overall"])
        self.assertFalse("all" in changed_data["metadata"])

        unchanged_data = NimbusExperiment.objects.get(
            slug="another-experiment"
        ).results_data

        self.assertTrue("all" in unchanged_data["daily"])
        self.assertFalse("control" in unchanged_data["daily"])
        self.assertFalse("all" in unchanged_data["other_metrics"])
