# Generated by Django 3.2.19 on 2023-06-17 23:43

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


def migrate_feature_config_data(apps, schema_editor):
    NimbusFeatureConfig = apps.get_model("experiments", "NimbusFeatureConfig")
    NimbusVersionedSchema = apps.get_model("experiments", "NimbusVersionedSchema")

    NimbusVersionedSchema.objects.bulk_create(
        NimbusVersionedSchema(
            feature_config=feature_config,
            version=None,
            schema=feature_config.schema,
            sets_prefs=feature_config.sets_prefs,
        )
        for feature_config in NimbusFeatureConfig.objects.all()
    )


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0239_alter_nimbusexperiment_experiment_targeting_blank"),
    ]

    operations = [
        migrations.CreateModel(
            name="NimbusVersionedSchema",
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
                ("version", models.CharField(max_length=255, null=True)),
                ("schema", models.TextField(blank=True, null=True)),
                (
                    "sets_prefs",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(default=list, max_length=255),
                        size=None,
                    ),
                ),
                (
                    "feature_config",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="schemas",
                        to="experiments.nimbusfeatureconfig",
                    ),
                ),
            ],
            options={
                "verbose_name": "Nimbus Versioned Schema",
                "verbose_name_plural": "Nimbus Versioned Schemas",
                "unique_together": {("feature_config", "version")},
            },
        ),
        migrations.RunPython(migrate_feature_config_data),
        migrations.RemoveField(
            model_name="nimbusfeatureconfig",
            name="read_only",
        ),
        migrations.RemoveField(
            model_name="nimbusfeatureconfig",
            name="schema",
        ),
        migrations.RemoveField(
            model_name="nimbusfeatureconfig",
            name="sets_prefs",
        ),
    ]
