# Generated by Django 3.1.3 on 2020-11-09 23:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0135_auto_20201105_2224"),
    ]

    operations = [
        migrations.AlterField(
            model_name="experimentemail",
            name="type",
            field=models.CharField(
                choices=[
                    ("starting", "starting"),
                    ("pausing", "pausing"),
                    ("ending", "ending"),
                    ("new comment", "new comment"),
                    ("intent to ship", "intent to ship"),
                ],
                max_length=255,
            ),
        ),
    ]
