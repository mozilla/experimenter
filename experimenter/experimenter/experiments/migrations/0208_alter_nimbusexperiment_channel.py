# Generated by Django 3.2.13 on 2022-05-05 19:34

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0207_nimbusexperiment_languages"),
    ]

    operations = [
        migrations.AlterField(
            model_name="nimbusexperiment",
            name="channel",
            field=models.CharField(
                choices=[
                    ("", "No Channel"),
                    ("default", "Unbranded"),
                    ("nightly", "Nightly"),
                    ("beta", "Beta"),
                    ("release", "Release"),
                    ("esr", "Esr"),
                    ("testflight", "Testflight"),
                ],
                max_length=255,
            ),
        ),
    ]
