import datetime

from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestBackfillEnrollmentEndDatesMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0347_alter_nimbusalert_alert_type",
    )
    migrate_to = (
        "experiments",
        "0348_backfill_enrollment_end_dates",
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

        earliest_paused = NimbusExperiment.objects.create(
            slug="earliest-paused",
            name="Paused with multiple published_dto pause changelogs",
            application="firefox-desktop",
            owner=owner,
            status="Live",
            is_paused=True,
            is_rollout=False,
        )
        NimbusChangeLog.objects.create(
            experiment=earliest_paused,
            changed_by=owner,
            changed_on=datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
            new_status="Live",
            new_publish_status="Review",
            message="Updated in Remote Settings",
            experiment_data={"published_dto": {"isEnrollmentPaused": True}},
        )
        NimbusChangeLog.objects.create(
            experiment=earliest_paused,
            changed_by=owner,
            changed_on=datetime.datetime(2026, 2, 1, tzinfo=datetime.UTC),
            new_status="Live",
            new_publish_status="Idle",
            message="Updated in Remote Settings",
            experiment_data={"published_dto": {"isEnrollmentPaused": True}},
        )

        fallback_paused = NimbusExperiment.objects.create(
            slug="fallback-paused",
            name="Paused with only is_paused fallback changelog",
            application="firefox-desktop",
            owner=owner,
            status="Complete",
            is_paused=True,
            is_rollout=False,
        )
        NimbusChangeLog.objects.create(
            experiment=fallback_paused,
            changed_by=owner,
            changed_on=datetime.datetime(2026, 3, 1, tzinfo=datetime.UTC),
            new_status="Live",
            new_publish_status="Idle",
            message="Updated in Remote Settings",
            experiment_data={"is_paused": True},
        )

        paused_rollout = NimbusExperiment.objects.create(
            slug="paused-rollout",
            name="Paused rollout, not an experiment",
            application="firefox-desktop",
            owner=owner,
            status="Live",
            is_paused=True,
            is_rollout=True,
        )
        NimbusChangeLog.objects.create(
            experiment=paused_rollout,
            changed_by=owner,
            changed_on=datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
            new_status="Live",
            new_publish_status="Idle",
            message="Updated in Remote Settings",
            experiment_data={"published_dto": {"isEnrollmentPaused": True}},
        )

        NimbusExperiment.objects.create(
            slug="never-paused-complete",
            name="Never paused, complete",
            application="firefox-desktop",
            owner=owner,
            status="Complete",
            is_paused=False,
            is_rollout=False,
        )

        already_dated = NimbusExperiment.objects.create(
            slug="already-dated",
            name="Paused but already has an enrollment end date",
            application="firefox-desktop",
            owner=owner,
            status="Live",
            is_paused=True,
            is_rollout=False,
            _enrollment_end_date=datetime.date(2026, 1, 15),
        )
        NimbusChangeLog.objects.create(
            experiment=already_dated,
            changed_by=owner,
            changed_on=datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
            new_status="Live",
            new_publish_status="Idle",
            message="Updated in Remote Settings",
            experiment_data={"published_dto": {"isEnrollmentPaused": True}},
        )

        unmatched_paused = NimbusExperiment.objects.create(
            slug="unmatched-paused",
            name="Paused with no matching changelog",
            application="firefox-desktop",
            owner=owner,
            status="Live",
            is_paused=True,
            is_rollout=False,
        )
        NimbusChangeLog.objects.create(
            experiment=unmatched_paused,
            changed_by=owner,
            changed_on=datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
            new_status="Live",
            new_publish_status="Idle",
            message="Some other message",
            experiment_data={"is_paused": False},
        )

    def test_migration(self):
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        earliest_paused = NimbusExperiment.objects.get(slug="earliest-paused")
        self.assertEqual(earliest_paused._enrollment_end_date, datetime.date(2026, 1, 1))

        fallback_paused = NimbusExperiment.objects.get(slug="fallback-paused")
        self.assertEqual(fallback_paused._enrollment_end_date, datetime.date(2026, 3, 1))

        paused_rollout = NimbusExperiment.objects.get(slug="paused-rollout")
        self.assertIsNone(paused_rollout._enrollment_end_date)

        never_paused_complete = NimbusExperiment.objects.get(slug="never-paused-complete")
        self.assertIsNone(never_paused_complete._enrollment_end_date)

        already_dated = NimbusExperiment.objects.get(slug="already-dated")
        self.assertEqual(already_dated._enrollment_end_date, datetime.date(2026, 1, 15))

        unmatched_paused = NimbusExperiment.objects.get(slug="unmatched-paused")
        self.assertIsNone(unmatched_paused._enrollment_end_date)
