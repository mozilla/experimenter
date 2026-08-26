from decimal import Decimal

from django.db import migrations

STARTED_STATUSES = ("Live", "Complete", "Disabled")
STAGED_PUBLISH_STATUSES = ("Approved", "Waiting")


def latest_changelog_dates(NimbusChangeLog, experiment_ids, old_status, new_status):
    return {
        experiment_id: changed_on.date()
        for experiment_id, changed_on in NimbusChangeLog.objects.filter(
            experiment_id__in=experiment_ids,
            old_status=old_status,
            new_status=new_status,
        )
        .order_by("changed_on")
        .values_list("experiment_id", "changed_on")
    }


def published_changelog_percents(NimbusChangeLog, experiment_ids):
    percents = {}
    for experiment_id, experiment_data in (
        NimbusChangeLog.objects.filter(
            experiment_id__in=experiment_ids,
            published_dto_changed=True,
        )
        .order_by("changed_on")
        .values_list("experiment_id", "experiment_data")
    ):
        percent = (experiment_data or {}).get("population_percent")
        if percent is not None:
            percents[experiment_id] = Decimal(str(percent))
    return percents


def live_and_pending_percents(rollout, published_percents):
    if not rollout.is_rollout_dirty:
        return rollout.population_percent, None

    published_percent = published_percents.get(rollout.id)

    if published_percent is None or published_percent == rollout.population_percent:
        return rollout.population_percent, None

    return published_percent, rollout.population_percent


def backfill_rollout_phases(apps, schema_editor):
    NimbusExperiment = apps.get_model("experiments", "NimbusExperiment")
    NimbusRolloutPhase = apps.get_model("experiments", "NimbusRolloutPhase")
    NimbusChangeLog = apps.get_model("experiments", "NimbusChangeLog")

    rollouts = list(
        NimbusExperiment.objects.filter(
            is_rollout=True,
            is_firefox_labs_opt_in=False,
            rollout_phases__isnull=True,
        )
        .only(
            "id",
            "status",
            "status_next",
            "publish_status",
            "population_percent",
            "is_rollout_dirty",
            "_start_date",
            "_end_date",
            "rollout_phase",
            "rollout_phase_next",
        )
        .order_by("id")
    )

    if not rollouts:
        return

    rollout_ids = [rollout.id for rollout in rollouts]
    launch_dates = latest_changelog_dates(NimbusChangeLog, rollout_ids, "Draft", "Live")
    end_dates = latest_changelog_dates(NimbusChangeLog, rollout_ids, "Live", "Complete")
    published_percents = published_changelog_percents(NimbusChangeLog, rollout_ids)

    started_rollouts = []
    staged_rollouts = []
    for rollout in rollouts:
        live_percent, pending_percent = live_and_pending_percents(
            rollout, published_percents
        )
        phase = NimbusRolloutPhase(
            experiment=rollout,
            population_percent=live_percent,
        )
        is_started = rollout.status in STARTED_STATUSES

        if is_started:
            start_date = rollout._start_date or launch_dates.get(rollout.id)
            phase.start_date = start_date
            phase.actual_start_date = start_date
            if rollout.status == "Complete":
                phase.end_date = rollout._end_date or end_dates.get(rollout.id)

        phase.save()

        if is_started:
            rollout.rollout_phase = phase
            started_rollouts.append(rollout)

            if pending_percent is not None:
                pending_phase = NimbusRolloutPhase.objects.create(
                    experiment=rollout,
                    population_percent=pending_percent,
                )
                if rollout.publish_status in STAGED_PUBLISH_STATUSES:
                    rollout.rollout_phase_next = pending_phase
                    staged_rollouts.append(rollout)
        elif is_launch_staged(rollout) and phase.population_percent:
            rollout.rollout_phase_next = phase
            staged_rollouts.append(rollout)

    NimbusExperiment.objects.bulk_update(
        started_rollouts, ["rollout_phase"], batch_size=500
    )
    NimbusExperiment.objects.bulk_update(
        staged_rollouts, ["rollout_phase_next"], batch_size=500
    )


def is_launch_staged(rollout):
    return (
        rollout.status == "Draft"
        and rollout.status_next == "Live"
        and rollout.publish_status in STAGED_PUBLISH_STATUSES
    )


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0339_force_weekly_retention_results_refetch"),
    ]

    operations = [
        migrations.RunPython(backfill_rollout_phases, migrations.RunPython.noop),
    ]
