# Generated by Django 3.2.5 on 2021-11-05 20:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0194_auto_20211102_1749"),
    ]

    operations = [
        migrations.AddField(
            model_name="nimbusexperiment",
            name="is_rollout",
            field=models.BooleanField(default=False),
        ),
    ]
