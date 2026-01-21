from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestFixPublishStatusPreviewMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0315_results_v3_overall_dict",
    )
    migrate_to = (
        "experiments",
        "0316_fix_publish_status_preview",
    )

    def prepare(self):
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        owner, _ = User.objects.get_or_create(
            username="test@example.com",
            defaults={"email": "test@example.com"},
        )

        NimbusExperiment.objects.create(
            slug="test-invalid-preview",
            name="Test Invalid Preview",
            application="firefox-desktop",
            owner=owner,
            status="Live",
            status_next="Complete",
            publish_status="Preview",
        )

        NimbusExperiment.objects.create(
            slug="test-valid-idle",
            name="Test Valid Idle",
            application="firefox-desktop",
            owner=owner,
            status="Draft",
            status_next=None,
            publish_status="Idle",
        )

        NimbusExperiment.objects.create(
            slug="test-valid-review",
            name="Test Valid Review",
            application="firefox-desktop",
            owner=owner,
            status="Draft",
            status_next=None,
            publish_status="Review",
        )

    def test_migration(self):
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        invalid_exp = NimbusExperiment.objects.get(slug="test-invalid-preview")
        self.assertEqual(invalid_exp.status, "Draft")
        self.assertIsNone(invalid_exp.status_next)
        self.assertEqual(invalid_exp.publish_status, "Idle")

        valid_idle = NimbusExperiment.objects.get(slug="test-valid-idle")
        self.assertEqual(valid_idle.status, "Draft")
        self.assertIsNone(valid_idle.status_next)
        self.assertEqual(valid_idle.publish_status, "Idle")

        valid_review = NimbusExperiment.objects.get(slug="test-valid-review")
        self.assertEqual(valid_review.status, "Draft")
        self.assertIsNone(valid_review.status_next)
        self.assertEqual(valid_review.publish_status, "Review")
