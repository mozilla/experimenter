# Generated by Django 3.0.7 on 2020-10-30 21:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0130_nimbusemail"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="nimbusexperiment",
            name="probe_sets",
        ),
        migrations.CreateModel(
            name="NimbusExperimentProbeSets",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("is_primary", models.BooleanField()),
                (
                    "experiment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="experiments.NimbusExperiment",
                    ),
                ),
                (
                    "probe_set",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="experiments.NimbusProbeSet",
                    ),
                ),
            ],
            options={
                "unique_together": {("experiment", "probe_set")},
            },
        ),
        migrations.AddField(
            model_name="nimbusexperiment",
            name="probe_sets",
            field=models.ManyToManyField(
                through="experiments.NimbusExperimentProbeSets",
                to="experiments.NimbusProbeSet",
            ),
        ),
    ]
