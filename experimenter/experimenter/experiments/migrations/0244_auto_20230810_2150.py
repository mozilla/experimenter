# Generated by Django 3.2.20 on 2023-08-10 21:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0243_nimbusexperiment_takeaways_metric_gain"),
    ]

    operations = [
        migrations.AlterField(
            model_name="nimbusexperiment",
            name="application",
            field=models.CharField(
                choices=[
                    ("firefox-desktop", "Firefox Desktop"),
                    ("fenix", "Firefox for Android (Fenix)"),
                    ("ios", "Firefox for iOS"),
                    ("focus-android", "Focus for Android"),
                    ("klar-android", "Klar for Android"),
                    ("focus-ios", "Focus for iOS"),
                    ("klar-ios", "Klar for iOS"),
                    ("monitor-web", "Monitor Web"),
                ],
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="nimbusfeatureconfig",
            name="application",
            field=models.CharField(
                blank=True,
                choices=[
                    ("firefox-desktop", "Firefox Desktop"),
                    ("fenix", "Firefox for Android (Fenix)"),
                    ("ios", "Firefox for iOS"),
                    ("focus-android", "Focus for Android"),
                    ("klar-android", "Klar for Android"),
                    ("focus-ios", "Focus for iOS"),
                    ("klar-ios", "Klar for iOS"),
                    ("monitor-web", "Monitor Web"),
                ],
                max_length=255,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="nimbusisolationgroup",
            name="application",
            field=models.CharField(
                choices=[
                    ("firefox-desktop", "Firefox Desktop"),
                    ("fenix", "Firefox for Android (Fenix)"),
                    ("ios", "Firefox for iOS"),
                    ("focus-android", "Focus for Android"),
                    ("klar-android", "Klar for Android"),
                    ("focus-ios", "Focus for iOS"),
                    ("klar-ios", "Klar for iOS"),
                    ("monitor-web", "Monitor Web"),
                ],
                max_length=255,
            ),
        ),
    ]
