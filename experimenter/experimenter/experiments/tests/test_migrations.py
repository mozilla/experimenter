from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestUnwedgeRolloutUpdateReviewMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0335_nimbusexperiment_sizing_data_updated_at",
    )
    migrate_to = (
        "experiments",
        "0336_unwedge_rollout_update_review",
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
            slug="wedged",
            name="Wedged rollout",
            application="firefox-desktop",
            owner=owner,
            is_rollout=True,
            status="Live",
            status_next="Live",
            publish_status="Review",
            is_rollout_dirty=False,
            is_paused=False,
        )
        NimbusExperiment.objects.create(
            slug="dirty-update-review",
            name="Legitimate dirty update review",
            application="firefox-desktop",
            owner=owner,
            is_rollout=True,
            status="Live",
            status_next="Live",
            publish_status="Review",
            is_rollout_dirty=True,
            is_paused=False,
        )
        NimbusExperiment.objects.create(
            slug="paused-end-enrollment-review",
            name="Legitimate paused end enrollment review",
            application="firefox-desktop",
            owner=owner,
            is_rollout=True,
            status="Live",
            status_next="Live",
            publish_status="Review",
            is_rollout_dirty=False,
            is_paused=True,
        )
        NimbusExperiment.objects.create(
            slug="non-rollout-review",
            name="Non-rollout experiment review",
            application="firefox-desktop",
            owner=owner,
            is_rollout=False,
            status="Live",
            status_next="Live",
            publish_status="Review",
            is_rollout_dirty=False,
            is_paused=False,
        )

    def test_migration(self):
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        wedged = NimbusExperiment.objects.get(slug="wedged")
        self.assertEqual(wedged.status, "Live")
        self.assertIsNone(wedged.status_next)
        self.assertEqual(wedged.publish_status, "Idle")
        self.assertFalse(wedged.is_rollout_dirty)
        self.assertFalse(wedged.is_paused)

        dirty = NimbusExperiment.objects.get(slug="dirty-update-review")
        self.assertEqual(dirty.status, "Live")
        self.assertEqual(dirty.status_next, "Live")
        self.assertEqual(dirty.publish_status, "Review")

        paused = NimbusExperiment.objects.get(slug="paused-end-enrollment-review")
        self.assertEqual(paused.status, "Live")
        self.assertEqual(paused.status_next, "Live")
        self.assertEqual(paused.publish_status, "Review")

        non_rollout = NimbusExperiment.objects.get(slug="non-rollout-review")
        self.assertEqual(non_rollout.status, "Live")
        self.assertEqual(non_rollout.status_next, "Live")
        self.assertEqual(non_rollout.publish_status, "Review")
