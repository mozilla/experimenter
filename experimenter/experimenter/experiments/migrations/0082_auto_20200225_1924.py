# Generated by Django 3.0.3 on 2020-02-25 19:24

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("experiments", "0081_remove_experiment_risk_internal_only")]

    operations = [
        migrations.RenameField(
            model_name="experiment",
            old_name="data_science_bugzilla_url",
            new_name="data_science_issue_url",
        )
    ]
