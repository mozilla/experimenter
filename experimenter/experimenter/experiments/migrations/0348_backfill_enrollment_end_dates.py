from django.db import migrations


def backfill_enrollment_end_dates(apps, schema_editor):
    NimbusExperiment = apps.get_model("experiments", "NimbusExperiment")

    experiments = NimbusExperiment.objects.filter(
        is_paused=True,
        is_rollout=False,
        status__in=["Live", "Complete"],
        _enrollment_end_date__isnull=True,
    )

    for experiment in experiments:
        paused_change = (
            experiment.changes.filter(
                experiment_data__published_dto__isEnrollmentPaused=True,
            )
            .order_by("changed_on")
            .first()
        )

        if paused_change is None:
            paused_change = (
                experiment.changes.filter(
                    message="Updated in Remote Settings",
                    experiment_data__is_paused=True,
                )
                .order_by("changed_on")
                .first()
            )

        if paused_change is None:
            continue

        experiment._enrollment_end_date = paused_change.changed_on.date()
        experiment.save(update_fields=["_enrollment_end_date"])


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0347_alter_nimbusalert_alert_type"),
    ]

    operations = [
        migrations.RunPython(backfill_enrollment_end_dates, migrations.RunPython.noop),
    ]
