from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestRemoveFocusKlarApplicationsMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0311_alter_nimbusexperiment_application_and_more",
    )
    migrate_to = (
        "experiments",
        "0312_delete_focus_klar_features",
    )

    def prepare(self):
        User = self.old_state.apps.get_model("auth", "User")
        NimbusFeatureConfig = self.old_state.apps.get_model(
            "experiments", "NimbusFeatureConfig"
        )
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        NimbusIsolationGroup = self.old_state.apps.get_model(
            "experiments", "NimbusIsolationGroup"
        )

        # Create a test user for experiment ownership
        owner, _ = User.objects.get_or_create(
            username="test@example.com",
            defaults={"email": "test@example.com"},
        )

        # Create NimbusFeatureConfigs for focus/klar applications
        NimbusFeatureConfig.objects.get_or_create(
            slug="no-feature-focus-android",
            defaults={
                "name": "No Feature Focus Android",
                "application": "focus-android",
            },
        )
        NimbusFeatureConfig.objects.get_or_create(
            slug="no-feature-klar-android",
            defaults={
                "name": "No Feature Klar Android",
                "application": "klar-android",
            },
        )
        NimbusFeatureConfig.objects.get_or_create(
            slug="no-feature-focus-ios",
            defaults={
                "name": "No Feature Focus iOS",
                "application": "focus-ios",
            },
        )
        NimbusFeatureConfig.objects.get_or_create(
            slug="no-feature-klar-ios",
            defaults={
                "name": "No Feature Klar iOS",
                "application": "klar-ios",
            },
        )

        # Create a fenix feature config to verify it's not deleted
        NimbusFeatureConfig.objects.get_or_create(
            slug="no-feature-fenix",
            defaults={
                "name": "No Feature Fenix",
                "application": "fenix",
            },
        )

        # Create NimbusExperiments for focus/klar applications
        NimbusExperiment.objects.get_or_create(
            slug="test-focus-android",
            defaults={
                "name": "Test Focus Android",
                "application": "focus-android",
                "owner": owner,
            },
        )
        NimbusExperiment.objects.get_or_create(
            slug="test-klar-android",
            defaults={
                "name": "Test Klar Android",
                "application": "klar-android",
                "owner": owner,
            },
        )
        NimbusExperiment.objects.get_or_create(
            slug="test-focus-ios",
            defaults={
                "name": "Test Focus iOS",
                "application": "focus-ios",
                "owner": owner,
            },
        )
        NimbusExperiment.objects.get_or_create(
            slug="test-klar-ios",
            defaults={
                "name": "Test Klar iOS",
                "application": "klar-ios",
                "owner": owner,
            },
        )

        # Create a fenix experiment to verify it's not deleted
        NimbusExperiment.objects.get_or_create(
            slug="test-fenix",
            defaults={
                "name": "Test Fenix",
                "application": "fenix",
                "owner": owner,
            },
        )

        # Create NimbusIsolationGroups for focus/klar applications
        NimbusIsolationGroup.objects.get_or_create(
            application="focus-android",
            name="test-group",
            instance=1,
        )
        NimbusIsolationGroup.objects.get_or_create(
            application="klar-android",
            name="test-group",
            instance=1,
        )
        NimbusIsolationGroup.objects.get_or_create(
            application="focus-ios",
            name="test-group",
            instance=1,
        )
        NimbusIsolationGroup.objects.get_or_create(
            application="klar-ios",
            name="test-group",
            instance=1,
        )

        # Create a fenix isolation group to verify it's not deleted
        NimbusIsolationGroup.objects.get_or_create(
            application="fenix",
            name="test-group",
            instance=1,
        )

    def test_migration(self):
        NimbusFeatureConfig = self.new_state.apps.get_model(
            "experiments", "NimbusFeatureConfig"
        )
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        NimbusIsolationGroup = self.new_state.apps.get_model(
            "experiments", "NimbusIsolationGroup"
        )

        # Verify NimbusFeatureConfigs are deleted
        self.assertFalse(
            NimbusFeatureConfig.objects.filter(slug="no-feature-focus-android").exists()
        )
        self.assertFalse(
            NimbusFeatureConfig.objects.filter(slug="no-feature-klar-android").exists()
        )
        self.assertFalse(
            NimbusFeatureConfig.objects.filter(slug="no-feature-focus-ios").exists()
        )
        self.assertFalse(
            NimbusFeatureConfig.objects.filter(slug="no-feature-klar-ios").exists()
        )

        self.assertTrue(
            NimbusFeatureConfig.objects.filter(slug="no-feature-fenix").exists()
        )

        # Verify NimbusExperiments are deleted
        self.assertFalse(
            NimbusExperiment.objects.filter(application="focus-android").exists()
        )
        self.assertFalse(
            NimbusExperiment.objects.filter(application="klar-android").exists()
        )
        self.assertFalse(
            NimbusExperiment.objects.filter(application="focus-ios").exists()
        )
        self.assertFalse(NimbusExperiment.objects.filter(application="klar-ios").exists())

        # Verify other applications still exist
        self.assertTrue(NimbusExperiment.objects.filter(application="fenix").exists())

        # Verify NimbusIsolationGroups are deleted
        self.assertFalse(
            NimbusIsolationGroup.objects.filter(application="focus-android").exists()
        )
        self.assertFalse(
            NimbusIsolationGroup.objects.filter(application="klar-android").exists()
        )
        self.assertFalse(
            NimbusIsolationGroup.objects.filter(application="focus-ios").exists()
        )
        self.assertFalse(
            NimbusIsolationGroup.objects.filter(application="klar-ios").exists()
        )

        # Verify other applications' isolation groups still exist
        self.assertTrue(NimbusIsolationGroup.objects.filter(application="fenix").exists())
