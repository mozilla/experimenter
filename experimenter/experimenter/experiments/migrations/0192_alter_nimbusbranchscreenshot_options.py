# Generated by Django 3.2.5 on 2021-10-04 21:31

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0191_auto_20211025_2014"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="nimbusbranchscreenshot",
            options={"ordering": ["id"]},
        ),
    ]
