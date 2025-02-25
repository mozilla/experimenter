# Generated by Django 3.0.7 on 2020-09-23 20:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0112_auto_20200922_2135"),
    ]

    operations = [
        migrations.CreateModel(
            name="NimbusBranch",
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
                ("enabled", models.BooleanField(default=True)),
                ("name", models.CharField(max_length=255)),
                ("slug", models.SlugField(max_length=255)),
                ("description", models.TextField(default="")),
                ("ratio", models.PositiveIntegerField(default=1)),
                ("value", models.TextField(blank=True, null=True)),
                (
                    "experiment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="branches",
                        to="experiments.NimbusExperiment",
                    ),
                ),
            ],
            options={
                "verbose_name": "Nimbus Branch",
                "verbose_name_plural": "Nimbus Branches",
                "unique_together": {("slug", "experiment")},
            },
        ),
        migrations.AddField(
            model_name="nimbusexperiment",
            name="control_branch",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="experiments.NimbusBranch",
            ),
        ),
    ]
