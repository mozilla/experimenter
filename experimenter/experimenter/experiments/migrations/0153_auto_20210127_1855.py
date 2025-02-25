# Generated by Django 3.1.5 on 2021-01-27 18:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0152_auto_20210119_1856"),
    ]

    operations = [
        migrations.AlterField(
            model_name="nimbusexperiment",
            name="firefox_min_version",
            field=models.CharField(
                choices=[
                    ("", "No Version"),
                    ("83.!", "Firefox 83"),
                    ("84.!", "Firefox 84"),
                    ("85.!", "Firefox 85"),
                    ("86.!", "Firefox 86"),
                    ("87.!", "Firefox 87"),
                    ("88.!", "Firefox 88"),
                    ("89.!", "Firefox 89"),
                    ("90.!", "Firefox 90"),
                    ("91.!", "Firefox 91"),
                    ("92.!", "Firefox 92"),
                    ("93.!", "Firefox 93"),
                    ("94.!", "Firefox 94"),
                    ("95.!", "Firefox 95"),
                    ("96.!", "Firefox 96"),
                    ("97.!", "Firefox 97"),
                    ("98.!", "Firefox 98"),
                    ("99.!", "Firefox 99"),
                    ("100.!", "Firefox 100"),
                ],
                default="",
                max_length=255,
            ),
        ),
    ]
