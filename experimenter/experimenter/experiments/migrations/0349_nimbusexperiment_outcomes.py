import django.contrib.postgres.fields
from django.db import migrations, models


def merge_outcomes(apps, schema_editor):
    NimbusExperiment = apps.get_model("experiments", "NimbusExperiment")

    for experiment in NimbusExperiment.objects.exclude(
        primary_outcomes=[], secondary_outcomes=[]
    ):
        outcomes = []
        for slug in experiment.primary_outcomes + experiment.secondary_outcomes:
            if slug not in outcomes:
                outcomes.append(slug)
        experiment.outcomes = outcomes
        experiment.save(update_fields=["outcomes"])


def split_outcomes(apps, schema_editor):
    # The split is not recorded anywhere, so everything comes back as primary.
    NimbusExperiment = apps.get_model("experiments", "NimbusExperiment")

    for experiment in NimbusExperiment.objects.exclude(outcomes=[]):
        experiment.primary_outcomes = experiment.outcomes
        experiment.save(update_fields=["primary_outcomes"])


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0348_backfill_enrollment_end_dates"),
    ]

    operations = [
        migrations.AddField(
            model_name="nimbusexperiment",
            name="outcomes",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=255),
                default=list,
                size=None,
                verbose_name="Outcomes",
            ),
        ),
        migrations.RunPython(merge_outcomes, split_outcomes),
        migrations.RemoveField(
            model_name="nimbusexperiment",
            name="primary_outcomes",
        ),
        migrations.RemoveField(
            model_name="nimbusexperiment",
            name="secondary_outcomes",
        ),
    ]
