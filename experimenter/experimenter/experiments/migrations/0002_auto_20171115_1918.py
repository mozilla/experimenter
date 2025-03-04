# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-11-15 19:18
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("projects", "0003_auto_20170630_1924"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("experiments", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Experiment",
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
                    "status",
                    models.CharField(
                        choices=[
                            ("Created", "Created"),
                            ("Pending", "Pending"),
                            ("Accepted", "Accepted"),
                            ("Launched", "Launched"),
                            ("Complete", "Complete"),
                            ("Rejected", "Rejected"),
                        ],
                        default="Created",
                        max_length=255,
                    ),
                ),
                ("pref_key", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "pref_type",
                    models.CharField(
                        choices=[
                            ("boolean", "boolean"),
                            ("integer", "integer"),
                            ("string", "string"),
                        ],
                        max_length=255,
                    ),
                ),
                (
                    "pref_branch",
                    models.CharField(
                        choices=[("default", "default"), ("user", "user")], max_length=255
                    ),
                ),
                ("firefox_version", models.CharField(max_length=255)),
                (
                    "firefox_channel",
                    models.CharField(
                        choices=[
                            ("Nightly", "Nightly"),
                            ("Beta", "Beta"),
                            ("Release", "Release"),
                        ],
                        default="Nightly",
                        max_length=255,
                    ),
                ),
                ("client_matching", models.TextField(default="")),
                ("name", models.CharField(max_length=255, unique=True)),
                ("slug", models.SlugField(max_length=255, unique=True)),
                ("objectives", models.TextField(default="")),
                ("analysis", models.TextField(blank=True, default="", null=True)),
                ("dashboard_url", models.URLField(blank=True, null=True)),
                ("dashboard_image_url", models.URLField(blank=True, null=True)),
                (
                    "population_percent",
                    models.DecimalField(decimal_places=4, default="0", max_digits=7),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="experiments",
                        to="projects.Project",
                    ),
                ),
            ],
            options={"verbose_name": "Experiment", "verbose_name_plural": "Experiments"},
        ),
        migrations.CreateModel(
            name="ExperimentChangeLog",
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
                ("changed_on", models.DateTimeField(auto_now_add=True)),
                (
                    "old_status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("Created", "Created"),
                            ("Pending", "Pending"),
                            ("Accepted", "Accepted"),
                            ("Launched", "Launched"),
                            ("Complete", "Complete"),
                            ("Rejected", "Rejected"),
                        ],
                        max_length=255,
                        null=True,
                    ),
                ),
                (
                    "new_status",
                    models.CharField(
                        choices=[
                            ("Created", "Created"),
                            ("Pending", "Pending"),
                            ("Accepted", "Accepted"),
                            ("Launched", "Launched"),
                            ("Complete", "Complete"),
                            ("Rejected", "Rejected"),
                        ],
                        max_length=255,
                    ),
                ),
                ("message", models.TextField(blank=True, null=True)),
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
                        to="experiments.Experiment",
                    ),
                ),
            ],
            options={
                "verbose_name": "Experiment Change Log",
                "verbose_name_plural": "Experiment Change Logs",
                "ordering": ("changed_on",),
            },
        ),
        migrations.CreateModel(
            name="ExperimentVariant",
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
                ("name", models.CharField(max_length=255)),
                ("slug", models.SlugField(max_length=255)),
                ("is_control", models.BooleanField(default=False)),
                ("description", models.TextField(default="")),
                ("ratio", models.PositiveIntegerField(default=1)),
                ("value", django.contrib.postgres.fields.jsonb.JSONField(default=False)),
                (
                    "experiment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="variants",
                        to="experiments.Experiment",
                    ),
                ),
            ],
            options={
                "verbose_name": "Experiment Variant",
                "verbose_name_plural": "Experiment Variants",
            },
        ),
        migrations.AlterUniqueTogether(
            name="experimentvariant",
            unique_together=set([("is_control", "experiment"), ("slug", "experiment")]),
        ),
    ]
