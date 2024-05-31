from django.db import migrations


def update_conclusion_recommendation_in_changelogs(apps, schema_editor):
    NimbusExperiment = apps.get_model("experiments", "NimbusExperiment")

    for experiment in NimbusExperiment.objects.all():

        for changelog in experiment.changes.all():
            experiment_data = changelog.experiment_data
            if "conclusion_recommendation" in experiment_data:
                old_value = experiment_data.pop("conclusion_recommendation")
                new_value = [old_value] if old_value else []
                experiment_data["conclusion_recommendations"] = new_value
                changelog.experiment_data = experiment_data
                changelog.save()


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0271_remove_nimbusexperiment_conclusion_recommendation"),
    ]

    operations = [
        migrations.RunPython(update_conclusion_recommendation_in_changelogs),
    ]
