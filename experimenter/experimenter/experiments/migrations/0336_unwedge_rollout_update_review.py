from django.db import migrations


def unwedge_rollout_update_review(apps, schema_editor):
    NimbusExperiment = apps.get_model("experiments", "NimbusExperiment")
    NimbusExperiment.objects.filter(
        is_rollout=True,
        status="Live",
        status_next="Live",
        publish_status="Review",
        is_rollout_dirty=False,
        is_paused=False,
    ).update(publish_status="Idle", status_next=None)


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0335_nimbusexperiment_sizing_data_updated_at"),
    ]

    operations = [
        migrations.RunPython(
            unwedge_rollout_update_review, migrations.RunPython.noop
        ),
    ]
