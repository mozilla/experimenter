# Generated by Django 3.0.7 on 2020-10-20 17:34

import django.contrib.postgres.fields.jsonb
import django.core.serializers.json
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import experimenter.experiments.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("experiments", "0126_auto_20201016_1710"),
    ]

    operations = [
        migrations.CreateModel(
            name="NimbusChangeLog",
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
                (
                    "changed_on",
                    models.DateTimeField(
                        default=experimenter.experiments.models.NimbusChangeLog.current_datetime
                    ),
                ),
                (
                    "old_status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("Draft", "Draft"),
                            ("Review", "Review"),
                            ("Accepted", "Accepted"),
                            ("Live", "Live"),
                            ("Complete", "Complete"),
                        ],
                        max_length=255,
                        null=True,
                    ),
                ),
                (
                    "new_status",
                    models.CharField(
                        choices=[
                            ("Draft", "Draft"),
                            ("Review", "Review"),
                            ("Accepted", "Accepted"),
                            ("Live", "Live"),
                            ("Complete", "Complete"),
                        ],
                        max_length=255,
                    ),
                ),
                ("message", models.TextField(blank=True, null=True)),
                (
                    "experiment_data",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        blank=True,
                        encoder=django.core.serializers.json.DjangoJSONEncoder,
                        null=True,
                    ),
                ),
                (
                    "changed_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "experiment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="changes",
                        to="experiments.NimbusExperiment",
                    ),
                ),
            ],
            options={
                "verbose_name": "Nimbus Experiment Change Log",
                "verbose_name_plural": "Nimbus Experiment Change Logs",
                "ordering": ("changed_on",),
            },
        ),
    ]
