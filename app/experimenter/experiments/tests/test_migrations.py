from django_test_migrations.contrib.unittest_case import MigratorTestCase

from experimenter.base.models import Language, Locale
from experimenter.experiments.models import NimbusExperiment as Experiment


class TestMigration(MigratorTestCase):
    migrate_from = ("experiments", "0211_alter_nimbusexperiment_targeting_config_slug")
    migrate_to = (
        "experiments",
        "0212_alter_nimbusexperiment_languages_field_for_mobile_client",
    )

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        Locale = self.old_state.apps.get_model("base", "Locale")
        Language = self.old_state.apps.get_model("base", "Language")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        user = User.objects.create(email="test@example.com")
        locale_en = Locale.objects.create(code="en", name="English")
        Language.objects.create(code="en", name="English")
        locale_ts = Locale.objects.create(code="ts", name="does not exist")

        desktop_experiment = NimbusExperiment.objects.create(
            owner=user,
            name="desktop experiment",
            slug="desktop_experiment",
            application=Experiment.Application.DESKTOP,
        )
        desktop_experiment.locales.add(locale_en.id)
        mobile_experiments_with_locales = NimbusExperiment.objects.create(
            owner=user,
            name="mobile experiment with locales",
            slug="mobile_experiment_with_locales",
            application=Experiment.Application.FOCUS_ANDROID,
        )
        mobile_experiments_with_locales.locales.add(locale_en.id, locale_ts.id)

        NimbusExperiment.objects.create(
            owner=user,
            name="mobile experiment without locales",
            slug="mobile_experiment_without_locales",
            application=Experiment.Application.FOCUS_IOS,
        )

    def test_migration(self):
        """Run the test itself."""
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        # get desktop experiment
        desktop_experiment = NimbusExperiment.objects.get(
            application=Experiment.Application.DESKTOP
        )

        self.assertEqual(
            desktop_experiment.locales.all()[0].code, Locale.objects.get(code="en").code
        )

        # get mobile experiment included locale filed
        mobile_experiment_with_locales = NimbusExperiment.objects.get(
            application=Experiment.Application.FOCUS_ANDROID
        )
        self.assertEqual(mobile_experiment_with_locales.locales.count(), 0)
        self.assertEqual(
            mobile_experiment_with_locales.languages.all()[0].code,
            Language.objects.get(code="en").code,
        )

        # get mobile experiment without locale field
        mobile_experiment_with_locales = NimbusExperiment.objects.get(
            application=Experiment.Application.FOCUS_IOS
        )
        self.assertEqual(mobile_experiment_with_locales.locales.count(), 0)
        self.assertEqual(mobile_experiment_with_locales.languages.count(), 0)
