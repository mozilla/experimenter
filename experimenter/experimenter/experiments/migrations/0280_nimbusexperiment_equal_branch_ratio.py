# Generated by Django 5.1.5 on 2025-03-04 16:34

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0279_nimbusexperiment__computed_end_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="nimbusexperiment",
            name="equal_branch_ratio",
            field=models.BooleanField(default=True),
        ),
    ]
