# Generated by Django 3.0.7 on 2020-11-05 15:47

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0133_prune_pop_percent_logs"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="nimbusexperiment",
            options={
                "verbose_name": "Nimbus Experiment",
                "verbose_name_plural": "Nimbus Experiments",
            },
        ),
        migrations.AlterField(
            model_name="nimbusexperiment",
            name="channels",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(
                    blank=True,
                    choices=[
                        ("beta", "Desktop Beta"),
                        ("nightly", "Desktop Nightly"),
                        ("release", "Desktop Release"),
                        ("org.mozilla.firefox.beta", "Fenix Beta"),
                        ("org.mozilla.fenix", "Fenix Nightly"),
                        ("org.mozilla.firefox", "Fenix Release"),
                    ],
                    max_length=255,
                    null=True,
                ),
                default=list,
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="nimbusexperiment",
            name="targeting_config_slug",
            field=models.CharField(
                blank=True,
                choices=[
                    ("all_english", "All English"),
                    ("us_only", "Us Only"),
                    ("first_run", "Targeting First Run"),
                    ("first_run_about_welcome", "Targeting First Run About Welcome"),
                ],
                max_length=255,
                null=True,
            ),
        ),
    ]
