import django.contrib.postgres.fields
from django.db import migrations, models

import experimenter.experiments.models
from experimenter.experiments.constants import ExperimentConstants


def forward_platform_string_to_array(apps, schema_editor):
    Experiment = apps.get_model("experiments", "Experiment")

    for experiment in Experiment.objects.all():
        if experiment.platform == ExperimentConstants.PLATFORM_ALL:
            experiment.platforms = ExperimentConstants.PLATFORMS_LIST
        else:
            experiment.platforms = [experiment.platform]

        experiment.save()


def reverse_platform_string_to_array(apps, schema_editor):
    Experiment = apps.get_model("experiments", "Experiment")

    for experiment in Experiment.objects.all():
        if len(experiment.platforms) == len(ExperimentConstants.PLATFORMS_LIST):
            experiment.platform = ExperimentConstants.PLATFORM_ALL
        else:
            experiment.platform = experiment.platforms[0]

        experiment.save()


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0090_add_platforms"),
    ]

    operations = [
        migrations.RunPython(
            forward_platform_string_to_array, reverse_platform_string_to_array
        ),
    ]
