import datetime
from decimal import Decimal

from django.utils import timezone
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


class TestForceWeeklyRetentionResultsRefetchMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0338_nimbusemail_rollout_phase_alter_nimbusemail_type",
    )
    migrate_to = (
        "experiments",
        "0339_force_weekly_retention_results_refetch",
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
            slug="with-analysis-start-time",
            name="With analysis start time",
            application="firefox-desktop",
            owner=owner,
            results_data={
                "v3": {
                    "metadata": {
                        "analysis_start_time": "2026-07-01T00:00:00+00:00",
                        "outcomes": {},
                    },
                    "overall": {},
                }
            },
        )
        NimbusExperiment.objects.create(
            slug="without-metadata",
            name="Without metadata",
            application="firefox-desktop",
            owner=owner,
            results_data={"v3": {"overall": {}}},
        )
        NimbusExperiment.objects.create(
            slug="null-metadata",
            name="Null metadata",
            application="firefox-desktop",
            owner=owner,
            results_data={"v3": {"metadata": None, "overall": {}}},
        )
        NimbusExperiment.objects.create(
            slug="no-results",
            name="No results",
            application="firefox-desktop",
            owner=owner,
            results_data=None,
        )

    def test_migration(self):
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )

        cleared = NimbusExperiment.objects.get(slug="with-analysis-start-time")
        self.assertIsNone(cleared.results_data["v3"]["metadata"]["analysis_start_time"])
        self.assertEqual(cleared.results_data["v3"]["metadata"]["outcomes"], {})
        self.assertEqual(cleared.results_data["v3"]["overall"], {})

        untouched = NimbusExperiment.objects.get(slug="without-metadata")
        self.assertEqual(untouched.results_data, {"v3": {"overall": {}}})

        null_metadata = NimbusExperiment.objects.get(slug="null-metadata")
        self.assertEqual(
            null_metadata.results_data, {"v3": {"metadata": None, "overall": {}}}
        )

        no_results = NimbusExperiment.objects.get(slug="no-results")
        self.assertIsNone(no_results.results_data)


class TestBackfillRolloutPhasesMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0341_nimbusexperiment_rollout_plan_name",
    )
    migrate_to = (
        "experiments",
        "0342_backfill_rollout_phases",
    )

    def prepare(self):
        User = self.old_state.apps.get_model("auth", "User")
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        NimbusRolloutPhase = self.old_state.apps.get_model(
            "experiments", "NimbusRolloutPhase"
        )
        NimbusChangeLog = self.old_state.apps.get_model("experiments", "NimbusChangeLog")

        self.owner, _ = User.objects.get_or_create(
            username="test@example.com",
            defaults={"email": "test@example.com"},
        )

        self.create_rollout(
            NimbusExperiment,
            slug="draft-rollout",
            status="Draft",
            population_percent=Decimal("35.0000"),
        )
        self.create_rollout(
            NimbusExperiment,
            slug="preview-rollout",
            status="Preview",
            population_percent=Decimal("5.0000"),
        )
        self.create_rollout(
            NimbusExperiment,
            slug="live-rollout",
            status="Live",
            population_percent=Decimal("50.0000"),
            _start_date=datetime.date(2026, 1, 5),
        )

        live_without_start_date = self.create_rollout(
            NimbusExperiment,
            slug="live-rollout-no-start-date",
            status="Live",
            population_percent=Decimal("20.0000"),
        )
        NimbusChangeLog.objects.create(
            experiment=live_without_start_date,
            changed_by=self.owner,
            changed_on=timezone.make_aware(datetime.datetime(2026, 2, 10, 12, 0)),
            old_status="Draft",
            new_status="Live",
            new_publish_status="Idle",
        )

        self.create_rollout(
            NimbusExperiment,
            slug="approved-launch-rollout",
            status="Draft",
            status_next="Live",
            publish_status="Approved",
            population_percent=Decimal("15.0000"),
        )
        self.create_rollout(
            NimbusExperiment,
            slug="review-launch-rollout",
            status="Draft",
            status_next="Live",
            publish_status="Review",
            population_percent=Decimal("15.0000"),
        )
        self.create_rollout(
            NimbusExperiment,
            slug="complete-rollout",
            status="Complete",
            population_percent=Decimal("100.0000"),
            _start_date=datetime.date(2026, 3, 1),
            _end_date=datetime.date(2026, 4, 1),
        )
        self.create_rollout(
            NimbusExperiment,
            slug="labs-rollout",
            status="Live",
            population_percent=Decimal("100.0000"),
            is_firefox_labs_opt_in=True,
            _start_date=datetime.date(2026, 6, 1),
        )
        self.create_rollout(
            NimbusExperiment,
            slug="experiment",
            status="Live",
            is_rollout=False,
            population_percent=Decimal("0.0000"),
        )

        already_phased = self.create_rollout(
            NimbusExperiment,
            slug="already-phased-rollout",
            status="Live",
            population_percent=Decimal("25.0000"),
        )
        NimbusRolloutPhase.objects.create(
            experiment=already_phased,
            population_percent=Decimal("25.0000"),
        )

        dirty = self.create_rollout(
            NimbusExperiment,
            slug="dirty-rollout",
            status="Live",
            population_percent=Decimal("30.0000"),
            is_rollout_dirty=True,
            _start_date=datetime.date(2026, 5, 1),
        )
        NimbusChangeLog.objects.create(
            experiment=dirty,
            changed_by=self.owner,
            changed_on=timezone.make_aware(datetime.datetime(2026, 5, 1, 12, 0)),
            old_status="Draft",
            new_status="Live",
            new_publish_status="Idle",
            published_dto_changed=True,
            experiment_data={"population_percent": "10.0000"},
        )

        dirty_in_flight = self.create_rollout(
            NimbusExperiment,
            slug="dirty-approved-rollout",
            status="Live",
            status_next="Live",
            publish_status="Approved",
            population_percent=Decimal("45.0000"),
            is_rollout_dirty=True,
            _start_date=datetime.date(2026, 5, 2),
        )
        NimbusChangeLog.objects.create(
            experiment=dirty_in_flight,
            changed_by=self.owner,
            changed_on=timezone.make_aware(datetime.datetime(2026, 5, 2, 12, 0)),
            old_status="Draft",
            new_status="Live",
            new_publish_status="Idle",
            published_dto_changed=True,
            experiment_data={"population_percent": "20.0000"},
        )

        dirty_unchanged = self.create_rollout(
            NimbusExperiment,
            slug="dirty-unchanged-population-rollout",
            status="Live",
            population_percent=Decimal("15.0000"),
            is_rollout_dirty=True,
            _start_date=datetime.date(2026, 5, 4),
        )
        NimbusChangeLog.objects.create(
            experiment=dirty_unchanged,
            changed_by=self.owner,
            changed_on=timezone.make_aware(datetime.datetime(2026, 5, 4, 12, 0)),
            old_status="Draft",
            new_status="Live",
            new_publish_status="Idle",
            published_dto_changed=True,
            experiment_data={"population_percent": "15.0000"},
        )

        self.create_rollout(
            NimbusExperiment,
            slug="dirty-no-published-data-rollout",
            status="Live",
            population_percent=Decimal("70.0000"),
            is_rollout_dirty=True,
            _start_date=datetime.date(2026, 5, 5),
        )

    def create_rollout(self, NimbusExperiment, slug, **kwargs):
        kwargs.setdefault("is_rollout", True)
        return NimbusExperiment.objects.create(
            slug=slug,
            name=slug,
            application="firefox-desktop",
            owner=self.owner,
            **kwargs,
        )

    def get_rollout(self, slug):
        NimbusExperiment = self.new_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        return NimbusExperiment.objects.get(slug=slug)

    def test_draft_rollout_gets_unstarted_phase(self):
        rollout = self.get_rollout("draft-rollout")
        phase = rollout.rollout_phases.get()

        self.assertEqual(phase.population_percent, Decimal("35.0000"))
        self.assertIsNone(phase.start_date)
        self.assertIsNone(phase.end_date)
        self.assertIsNone(phase.actual_start_date)
        self.assertIsNone(rollout.rollout_phase)
        self.assertIsNone(rollout.rollout_phase_next)

    def test_preview_rollout_gets_unstarted_phase(self):
        rollout = self.get_rollout("preview-rollout")
        phase = rollout.rollout_phases.get()

        self.assertEqual(phase.population_percent, Decimal("5.0000"))
        self.assertIsNone(phase.actual_start_date)
        self.assertIsNone(rollout.rollout_phase)

    def test_approved_launch_rollout_gets_staged_next_phase(self):
        rollout = self.get_rollout("approved-launch-rollout")
        phase = rollout.rollout_phases.get()

        self.assertIsNone(rollout.rollout_phase)
        self.assertEqual(rollout.rollout_phase_next, phase)
        self.assertIsNone(phase.actual_start_date)

    def test_review_launch_rollout_does_not_stage_next_phase(self):
        rollout = self.get_rollout("review-launch-rollout")

        self.assertEqual(rollout.rollout_phases.count(), 1)
        self.assertIsNone(rollout.rollout_phase)
        self.assertIsNone(rollout.rollout_phase_next)

    def test_live_rollout_gets_current_phase(self):
        rollout = self.get_rollout("live-rollout")
        phase = rollout.rollout_phases.get()

        self.assertEqual(phase.population_percent, Decimal("50.0000"))
        self.assertEqual(phase.start_date, datetime.date(2026, 1, 5))
        self.assertEqual(phase.actual_start_date, datetime.date(2026, 1, 5))
        self.assertIsNone(phase.end_date)
        self.assertEqual(rollout.rollout_phase, phase)
        self.assertIsNone(rollout.rollout_phase_next)

    def test_live_rollout_start_date_falls_back_to_changelog(self):
        rollout = self.get_rollout("live-rollout-no-start-date")
        phase = rollout.rollout_phases.get()

        self.assertEqual(phase.start_date, datetime.date(2026, 2, 10))
        self.assertEqual(phase.actual_start_date, datetime.date(2026, 2, 10))
        self.assertEqual(rollout.rollout_phase, phase)

    def test_complete_rollout_gets_dated_phase(self):
        rollout = self.get_rollout("complete-rollout")
        phase = rollout.rollout_phases.get()

        self.assertEqual(phase.population_percent, Decimal("100.0000"))
        self.assertEqual(phase.start_date, datetime.date(2026, 3, 1))
        self.assertEqual(phase.actual_start_date, datetime.date(2026, 3, 1))
        self.assertEqual(phase.end_date, datetime.date(2026, 4, 1))
        self.assertEqual(rollout.rollout_phase, phase)

    def test_labs_rollout_is_skipped(self):
        rollout = self.get_rollout("labs-rollout")

        self.assertEqual(rollout.rollout_phases.count(), 0)
        self.assertIsNone(rollout.rollout_phase)

    def test_experiment_is_skipped(self):
        rollout = self.get_rollout("experiment")

        self.assertEqual(rollout.rollout_phases.count(), 0)
        self.assertIsNone(rollout.rollout_phase)

    def test_rollout_with_existing_phases_is_untouched(self):
        rollout = self.get_rollout("already-phased-rollout")

        self.assertEqual(rollout.rollout_phases.count(), 1)
        self.assertIsNone(rollout.rollout_phase)

    def test_dirty_rollout_phase_uses_published_percent(self):
        rollout = self.get_rollout("dirty-rollout")
        current, pending = rollout.rollout_phases.order_by("id")

        self.assertEqual(current.population_percent, Decimal("10.0000"))
        self.assertEqual(current.actual_start_date, datetime.date(2026, 5, 1))
        self.assertEqual(rollout.rollout_phase, current)

        self.assertEqual(pending.population_percent, Decimal("30.0000"))
        self.assertIsNone(pending.actual_start_date)
        self.assertIsNone(rollout.rollout_phase_next)

    def test_dirty_rollout_with_approved_update_stages_pending_phase(self):
        rollout = self.get_rollout("dirty-approved-rollout")
        current, pending = rollout.rollout_phases.order_by("id")

        self.assertEqual(current.population_percent, Decimal("20.0000"))
        self.assertEqual(rollout.rollout_phase, current)

        self.assertEqual(pending.population_percent, Decimal("45.0000"))
        self.assertEqual(rollout.rollout_phase_next, pending)

    def test_dirty_rollout_without_population_change_gets_one_phase(self):
        rollout = self.get_rollout("dirty-unchanged-population-rollout")
        phase = rollout.rollout_phases.get()

        self.assertEqual(phase.population_percent, Decimal("15.0000"))
        self.assertEqual(rollout.rollout_phase, phase)
        self.assertIsNone(rollout.rollout_phase_next)

    def test_dirty_rollout_without_published_data_uses_current_percent(self):
        rollout = self.get_rollout("dirty-no-published-data-rollout")
        phase = rollout.rollout_phases.get()

        self.assertEqual(phase.population_percent, Decimal("70.0000"))
        self.assertEqual(rollout.rollout_phase, phase)
        self.assertIsNone(rollout.rollout_phase_next)
