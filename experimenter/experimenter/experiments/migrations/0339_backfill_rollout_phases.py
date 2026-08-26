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

    started_rollouts = []
    staged_rollouts = []
    for rollout in rollouts:
        phase = NimbusRolloutPhase(
            experiment=rollout,
            population_percent=rollout.population_percent,
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
        ("experiments", "0338_nimbusemail_rollout_phase_alter_nimbusemail_type"),
    ]

    operations = [
        migrations.RunPython(backfill_rollout_phases, migrations.RunPython.noop),
    ]
