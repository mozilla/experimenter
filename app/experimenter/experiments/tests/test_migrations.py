from django_test_migrations.contrib.unittest_case import MigratorTestCase

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment as Experiment


class TestMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0214_migrate_sticky",
    )
    migrate_to = (
        "experiments",
        "0215_update_removed_targeting_config_slugs",
    )

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        user = User.objects.create(email="test@example.com")

        NimbusExperiment.objects.create(
            owner=user,
            name="urlbar_firefox_suggest_us_en",
            slug="urlbar_firefox_suggest_us_en",
            application=Experiment.Application.DESKTOP,
            status=NimbusConstants.Status.DRAFT,
            targeting_config_slug="urlbar_firefox_suggest_us_en",
        )

        NimbusExperiment.objects.create(
            owner=user,
            name="another experiment",
            slug="another experiment",
            application=Experiment.Application.DESKTOP,
            status=NimbusConstants.Status.DRAFT,
            targeting_config_slug="another_targeting",
        )

    def test_migration(self):
        """Run the test itself."""
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        self.assertTrue(
            NimbusExperiment.objects.filter(
                targeting_config_slug="urlbar_firefox_suggest"
            ).exists()
        )
        self.assertFalse(
            NimbusExperiment.objects.filter(
                targeting_config_slug="urlbar_firefox_suggest_en_us"
            ).exists()
        )
        self.assertTrue(
            NimbusExperiment.objects.filter(
                targeting_config_slug="another_targeting"
            ).exists()
        )
