# Generated by Django 3.2.14 on 2022-07-27 19:12

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0215_update_removed_targeting_config_slugs"),
    ]

    operations = [
        migrations.AddField(
            model_name="nimbusexperiment",
            name="is_first_run",
            field=models.BooleanField(default=False),
        ),
    ]
