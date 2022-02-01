# Generated by Django 3.2.11 on 2022-02-01 08:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0203_auto_20220113_1853"),
    ]

    operations = [
        migrations.AlterField(
            model_name="nimbusexperiment",
            name="firefox_max_version",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AlterField(
            model_name="nimbusexperiment",
            name="firefox_min_version",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
