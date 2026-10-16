from django.conf import settings
from django.db import migrations

RECOVERED_MESSAGE = "Recovered from stuck end enrollment review"


def recover_stuck_end_enrollment_reviews(apps, schema_editor):
    NimbusExperiment = apps.get_model("experiments", "NimbusExperiment")
    NimbusChangeLog = apps.get_model("experiments", "NimbusChangeLog")
    User = apps.get_model("auth", "User")

    experiments = NimbusExperiment.objects.filter(
        status="Live",
        status_next="Live",
        publish_status="Review",
        is_paused=True,
        is_rollout=False,
        published_dto__isEnrollmentPaused=True,
    )

    if not experiments.exists():
        return

    kinto_user, _ = User.objects.get_or_create(
        email=settings.KINTO_DEFAULT_CHANGELOG_USER,
        username=settings.KINTO_DEFAULT_CHANGELOG_USER,
    )

    for experiment in experiments:
        latest_change = experiment.changes.order_by("-changed_on").first()
        if latest_change is not None:
            old_status = latest_change.new_status
            old_status_next = latest_change.new_status_next
            old_publish_status = latest_change.new_publish_status
            experiment_data = dict(latest_change.experiment_data or {})
        else:
            old_status = experiment.status
            old_status_next = experiment.status_next
            old_publish_status = experiment.publish_status
            experiment_data = {}

        experiment.status_next = None
        experiment.publish_status = "Idle"
        experiment.save(
            update_fields=["status_next", "publish_status", "_updated_date_time"]
        )

        experiment_data["status_next"] = None
        experiment_data["publish_status"] = "Idle"

        NimbusChangeLog.objects.create(
            experiment=experiment,
            changed_by=kinto_user,
            old_status=old_status,
            old_status_next=old_status_next,
            old_publish_status=old_publish_status,
            new_status="Live",
            new_status_next=None,
            new_publish_status="Idle",
            message=RECOVERED_MESSAGE,
            experiment_data=experiment_data,
            published_dto_changed=False,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0345_nimbusexperiment_analysis_data_and_more"),
    ]

    operations = [
        migrations.RunPython(
            recover_stuck_end_enrollment_reviews, migrations.RunPython.noop
        ),
    ]
