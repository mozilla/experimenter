# Generated by Django 3.2.16 on 2023-02-07 14:52

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0227_nimbusfeatureconfig_enabled"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="nimbusbranchfeaturevalue",
            name="enabled",
        ),
    ]
