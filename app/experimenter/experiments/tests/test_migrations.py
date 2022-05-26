from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestMigration(MigratorTestCase):
    migrate_from = ("experiments", "0208_alter_nimbusexperiment_channel")
    migrate_to = ("legacy_experiments", "0001_initial")

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        Experiment = self.old_state.apps.get_model("experiments", "Experiment")
        ExperimentVariant = self.old_state.apps.get_model(
            "experiments", "ExperimentVariant"
        )
        ExperimentEmail = self.old_state.apps.get_model("experiments", "ExperimentEmail")
        ExperimentComment = self.old_state.apps.get_model(
            "experiments", "ExperimentComment"
        )
        ExperimentChangeLog = self.old_state.apps.get_model(
            "experiments", "ExperimentChangeLog"
        )
        VariantPreferences = self.old_state.apps.get_model(
            "experiments", "VariantPreferences"
        )
        RolloutPreference = self.old_state.apps.get_model(
            "experiments", "RolloutPreference"
        )

        user = User.objects.create(email="test@example.com")
        experiment = Experiment.objects.create(slug="test_experiment")
        variant = ExperimentVariant.objects.create(
            experiment_id=experiment.id, slug="test_variant"
        )
        ExperimentEmail.objects.create(experiment_id=experiment.id, type="test_email")
        ExperimentComment.objects.create(
            experiment_id=experiment.id, created_by_id=user.id, text="test_comment"
        )
        ExperimentChangeLog.objects.create(
            experiment_id=experiment.id, changed_by_id=user.id, new_status="test_status"
        )
        VariantPreferences.objects.create(
            variant_id=variant.id,
            pref_branch="test_branch",
            pref_name="test_name",
            pref_type="test_type",
            pref_value="test_value",
        )
        RolloutPreference.objects.create(
            experiment_id=experiment.id,
            pref_name="test_name",
            pref_type="test_type",
            pref_value="test_value",
        )

    def test_migration(self):
        """Run the test itself."""
        User = self.new_state.apps.get_model("auth", "User")
        Experiment = self.new_state.apps.get_model("legacy_experiments", "Experiment")
        ExperimentVariant = self.new_state.apps.get_model(
            "legacy_experiments", "ExperimentVariant"
        )
        ExperimentEmail = self.new_state.apps.get_model(
            "legacy_experiments", "ExperimentEmail"
        )
        ExperimentComment = self.new_state.apps.get_model(
            "legacy_experiments", "ExperimentComment"
        )
        ExperimentChangeLog = self.new_state.apps.get_model(
            "legacy_experiments", "ExperimentChangeLog"
        )
        VariantPreferences = self.new_state.apps.get_model(
            "legacy_experiments", "VariantPreferences"
        )
        RolloutPreference = self.new_state.apps.get_model(
            "legacy_experiments", "RolloutPreference"
        )

        user = User.objects.get(email="test@example.com")
        experiment = Experiment.objects.get(slug="test_experiment")
        variant = ExperimentVariant.objects.get(
            experiment_id=experiment.id, slug="test_variant"
        )
        ExperimentEmail.objects.get(experiment_id=experiment.id, type="test_email")
        ExperimentComment.objects.get(
            experiment_id=experiment.id, created_by_id=user.id, text="test_comment"
        )
        ExperimentChangeLog.objects.get(
            experiment_id=experiment.id,
            changed_by_id=user.id,
            new_status="test_status",
        )
        VariantPreferences.objects.get(
            variant_id=variant.id,
            pref_branch="test_branch",
            pref_name="test_name",
            pref_type="test_type",
            pref_value="test_value",
        )
        RolloutPreference.objects.get(
            experiment_id=experiment.id,
            pref_name="test_name",
            pref_type="test_type",
            pref_value="test_value",
        )
