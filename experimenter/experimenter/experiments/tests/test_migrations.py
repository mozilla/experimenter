from django.conf import settings
from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestRecoverStuckEndEnrollmentReviewsMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0345_nimbusexperiment_analysis_data_and_more",
    )
    migrate_to = (
        "experiments",
        "0346_recover_stuck_end_enrollment_reviews",
    )

    def prepare(self):
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        NimbusChangeLog = self.old_state.apps.get_model("experiments", "NimbusChangeLog")

        owner, _ = User.objects.get_or_create(
            username="test@example.com",
            defaults={"email": "test@example.com"},
        )

        stuck = NimbusExperiment.objects.create(
            slug="stuck",
            name="Stuck end enrollment review",
            application="firefox-desktop",
            owner=owner,
            status="Live",
            status_next="Live",
            publish_status="Review",
            is_paused=True,
            is_rollout=False,
            published_dto={"id": "stuck", "isEnrollmentPaused": True},
        )
        NimbusChangeLog.objects.create(
            experiment=stuck,
            changed_by=owner,
            old_status="Live",
            old_status_next="Live",
            old_publish_status="Review",
            new_status="Live",
            new_status_next="Live",
            new_publish_status="Review",
            message="Resynchronized from Remote Settings",
            experiment_data={
                "slug": "stuck",
                "status": "Live",
                "status_next": "Live",
                "publish_status": "Review",
                "is_paused": True,
            },
        )

        NimbusExperiment.objects.create(
            slug="labs-rollout",
            name="Paused Labs rollout with pending update",
            application="firefox-desktop",
            owner=owner,
            status="Live",
            status_next="Live",
            publish_status="Review",
            is_paused=True,
            is_rollout=True,
            is_firefox_labs_opt_in=True,
            published_dto={"id": "labs-rollout", "isEnrollmentPaused": True},
        )

        NimbusExperiment.objects.create(
            slug="pending-end-enrollment",
            name="Pending end enrollment request",
            application="firefox-desktop",
            owner=owner,
            status="Live",
            status_next="Live",
            publish_status="Review",
            is_paused=True,
            is_rollout=False,
            published_dto={"id": "pending-end-enrollment", "isEnrollmentPaused": False},
        )

    def test_migration(self):
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        NimbusChangeLog = self.new_state.apps.get_model("experiments", "NimbusChangeLog")

        stuck = NimbusExperiment.objects.get(slug="stuck")
        self.assertEqual(stuck.status, "Live")
        self.assertIsNone(stuck.status_next)
        self.assertEqual(stuck.publish_status, "Idle")

        recovery_change = NimbusChangeLog.objects.get(
            experiment=stuck,
            message="Recovered from stuck end enrollment review",
        )
        self.assertEqual(
            recovery_change.changed_by.email, settings.KINTO_DEFAULT_CHANGELOG_USER
        )
        self.assertEqual(recovery_change.old_status, "Live")
        self.assertEqual(recovery_change.old_status_next, "Live")
        self.assertEqual(recovery_change.old_publish_status, "Review")
        self.assertEqual(recovery_change.new_status, "Live")
        self.assertIsNone(recovery_change.new_status_next)
        self.assertEqual(recovery_change.new_publish_status, "Idle")
        self.assertFalse(recovery_change.published_dto_changed)
        self.assertEqual(
            recovery_change.experiment_data,
            {
                "slug": "stuck",
                "status": "Live",
                "status_next": None,
                "publish_status": "Idle",
                "is_paused": True,
            },
        )

        for slug in ("labs-rollout", "pending-end-enrollment"):
            experiment = NimbusExperiment.objects.get(slug=slug)
            self.assertEqual(experiment.status, "Live")
            self.assertEqual(experiment.status_next, "Live")
            self.assertEqual(experiment.publish_status, "Review")
            self.assertFalse(
                NimbusChangeLog.objects.filter(experiment=experiment).exists()
            )
