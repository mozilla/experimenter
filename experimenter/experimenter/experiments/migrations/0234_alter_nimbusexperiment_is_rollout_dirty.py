# Generated by Django 3.2.19 on 2023-05-12 16:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0233_auto_20230510_1543"),
    ]

    operations = [
        migrations.AlterField(
            model_name="nimbusexperiment",
            name="is_rollout_dirty",
            field=models.BooleanField(default=False),
        ),
    ]
