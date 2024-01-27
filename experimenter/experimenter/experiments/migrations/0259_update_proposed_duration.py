from django.db import migrations, models


def update_proposed_duration(apps, schema_editor):
    NimbusExperiment = apps.get_model("experiments", "NimbusExperiment")
    # Update proposed_duration where it's less than proposed_enrollment
    NimbusExperiment.objects.filter(
        proposed_duration__lt=models.F("proposed_enrollment")
    ).update(proposed_duration=models.F("proposed_enrollment"))


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0258_nimbusexperiment_subscribers"),
    ]

    operations = [
        migrations.RunPython(update_proposed_duration),
    ]
