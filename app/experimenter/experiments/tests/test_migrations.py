from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestMigration0181Forward(MigratorTestCase):
    migrate_from = ("experiments", "0197_auto_20211109_2000")
    migrate_to = ("experiments", "0198_auto_20211110_1527")

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        NimbusBranch = self.old_state.apps.get_model("experiments", "NimbusBranch")
        NimbusFeatureConfig = self.old_state.apps.get_model(
            "experiments", "NimbusFeatureConfig"
        )

        owner = User.objects.create(email="owner@example.com")

        self.feature_config = NimbusFeatureConfig.objects.create()

        experiment = NimbusExperiment.objects.create(
            owner=owner, slug="experiment", feature_config=self.feature_config
        )

        experiment.reference_branch = NimbusBranch.objects.create(
            experiment=experiment,
            slug="control",
            feature_enabled=False,
            feature_value="control",
        )
        experiment.save()

        NimbusBranch.objects.create(
            experiment=experiment,
            slug="treatment",
            feature_enabled=True,
            feature_value="treatment",
        )

    def test_migration(self):
        """Run the test itself."""
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        experiment = NimbusExperiment.objects.get(slug="experiment")

        self.assertEqual(experiment.feature_configs.get().id, self.feature_config.id)

        reference_feature_value = experiment.reference_branch.feature_values.get()
        self.assertEqual(
            reference_feature_value.feature_config.id, self.feature_config.id
        )
        self.assertEqual(reference_feature_value.enabled, False)
        self.assertEqual(reference_feature_value.value, "control")

        treatment_feature_value = experiment.branches.get(
            slug="treatment"
        ).feature_values.get()
        self.assertEqual(
            treatment_feature_value.feature_config.id, self.feature_config.id
        )
        self.assertEqual(treatment_feature_value.enabled, True)
        self.assertEqual(treatment_feature_value.value, "treatment")
