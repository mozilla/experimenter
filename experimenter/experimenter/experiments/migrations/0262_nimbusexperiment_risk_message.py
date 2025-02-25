# Generated by Django 3.2.24 on 2024-02-21 00:25

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0261_nimbusversionedschema_set_pref_vars"),
    ]

    operations = [
        migrations.AddField(
            model_name="nimbusexperiment",
            name="risk_message",
            field=models.BooleanField(
                blank=True, default=None, null=True, verbose_name="Is a Message Risk Flag"
            ),
        ),
    ]
