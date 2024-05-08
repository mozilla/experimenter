from django.db import migrations, models
import json


def migrate_conclusion_recommendations(apps, schema_editor):
    NimbusExperiment = apps.get_model("experiments", "NimbusExperiment")

    for experiment in NimbusExperiment.objects.all():
        old_value = experiment.conclusion_recommendation
        new_value = [old_value] if old_value else []
        experiment.conclusion_recommendations = new_value
        experiment.save()


class Migration(migrations.Migration):

    dependencies = [
        (
            "experiments",
            "0269_nimbusexperiment_conclusion_recommendations",
        ),
    ]

    operations = [
        migrations.RunPython(migrate_conclusion_recommendations),
    ]
