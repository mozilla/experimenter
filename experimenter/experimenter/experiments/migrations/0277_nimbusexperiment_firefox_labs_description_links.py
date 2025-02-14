# Generated by Django 5.1.5 on 2025-02-03 21:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0276_nimbusexperiment_requires_restart"),
    ]

    operations = [
        migrations.AddField(
            model_name="nimbusexperiment",
            name="firefox_labs_description_links",
            field=models.JSONField(
                blank=True,
                default=None,
                null=True,
                verbose_name="Firefox Labs Description Links",
            ),
        ),
    ]
