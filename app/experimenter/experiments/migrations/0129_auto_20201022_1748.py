# Generated by Django 3.0.7 on 2020-10-22 17:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0128_nimbusexperiment_total_enrolled_clients"),
    ]

    operations = [
        migrations.RenameField(
            model_name="nimbusexperiment",
            old_name="control_branch",
            new_name="reference_branch",
        ),
    ]
