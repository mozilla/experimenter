from django.db import migrations


def clear_monitoring_data(apps, schema_editor):
    NimbusExperiment = apps.get_model("experiments", "NimbusExperiment")
    NimbusExperiment.objects.exclude(status__in=["Live", "Complete"]).update(
        monitoring_data=None
    )


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0325_remove_nimbusexperiment_klaatu_fields"),
    ]

    operations = [
        migrations.RunPython(clear_monitoring_data),
    ]
