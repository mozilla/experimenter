from django.db import migrations


def clear_monitoring_data(apps, schema_editor):
    NimbusExperiment = apps.get_model("experiments", "NimbusExperiment")
    NimbusExperiment.objects.exclude(status__in=["Live", "Complete"]).update(
        monitoring_data=None
    )


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0326_alter_nimbusexperiment_next_steps_and_more"),
    ]

    operations = [
        migrations.RunPython(clear_monitoring_data),
    ]
