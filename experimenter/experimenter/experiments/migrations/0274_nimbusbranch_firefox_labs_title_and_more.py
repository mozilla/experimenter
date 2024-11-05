# Generated by Django 5.1.1 on 2024-11-01 19:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0273_nimbusexperiment_segments"),
    ]

    operations = [
        migrations.AddField(
            model_name="nimbusbranch",
            name="firefox_labs_title",
            field=models.TextField(
                blank=True, null=True, verbose_name="Firefox Labs experiment title"
            ),
        ),
        migrations.AddField(
            model_name="nimbusexperiment",
            name="firefox_labs_description",
            field=models.TextField(
                blank=True,
                null=True,
                verbose_name="Firefox Labs experiment description",
            ),
        ),
        migrations.AddField(
            model_name="nimbusexperiment",
            name="firefox_labs_title",
            field=models.TextField(
                blank=True, null=True, verbose_name="Firefox Labs experiment title"
            ),
        ),
        migrations.AddField(
            model_name="nimbusexperiment",
            name="is_firefox_labs_opt_in",
            field=models.BooleanField(
                default=False, verbose_name="Is Firefox Labs Opt In"
            ),
        ),
    ]
