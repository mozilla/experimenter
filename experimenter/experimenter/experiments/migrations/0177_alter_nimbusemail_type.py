# Generated by Django 3.2.5 on 2021-07-16 13:46

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0176_auto_20210705_2257"),
    ]

    operations = [
        migrations.AlterField(
            model_name="nimbusemail",
            name="type",
            field=models.CharField(
                choices=[
                    ("experiment end", "Experiment End"),
                    ("enrollment end", "Enrollment End"),
                ],
                max_length=255,
            ),
        ),
    ]
