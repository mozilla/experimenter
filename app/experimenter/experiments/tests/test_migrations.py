from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestMigration0181Forward(MigratorTestCase):
    migrate_from = ("experiments", "0198_auto_20211110_1527")
    migrate_to = ("experiments", "0199_alter_nimbusbranchfeaturevalue_value")

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        NimbusBranch = self.old_state.apps.get_model("experiments", "NimbusBranch")
        NimbusBranchFeatureValue = self.old_state.apps.get_model(
            "experiments", "NimbusBranchFeatureValue"
        )

        owner = User.objects.create(email="owner@example.com")

        experiment = NimbusExperiment.objects.create(
            owner=owner,
            name="experiment",
            slug="experiment",
        )

        branch_with_value = NimbusBranch.objects.create(
            experiment=experiment,
            slug="control",
        )
        NimbusBranchFeatureValue.objects.create(branch=branch_with_value, value="value")

        branch_without_value = NimbusBranch.objects.create(
            experiment=experiment,
            slug="treatment",
        )
        NimbusBranchFeatureValue.objects.create(branch=branch_without_value, value=None)

    def test_migration(self):
        """Run the test itself."""
        NimbusBranchFeatureValue = self.new_state.apps.get_model(
            "experiments", "NimbusBranchFeatureValue"
        )

        self.assertFalse(NimbusBranchFeatureValue.objects.filter(value=None).exists())
        self.assertTrue(NimbusBranchFeatureValue.objects.filter(value="value").exists())
        self.assertTrue(NimbusBranchFeatureValue.objects.filter(value="").exists())
