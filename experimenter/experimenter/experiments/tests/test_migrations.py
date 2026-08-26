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


class TestBackfillRolloutPhasesMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0338_nimbusemail_rollout_phase_alter_nimbusemail_type",
    )
    migrate_to = (
        "experiments",
        "0339_backfill_rollout_phases",
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
            slug="approved-launch-zero-population-rollout",
            status="Draft",
            status_next="Live",
            publish_status="Approved",
            population_percent=Decimal("0.0000"),
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

    def test_approved_launch_rollout_at_zero_population_is_not_staged(self):
        rollout = self.get_rollout("approved-launch-zero-population-rollout")

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
