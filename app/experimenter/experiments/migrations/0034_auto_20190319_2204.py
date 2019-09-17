# Generated by Django 2.1.7 on 2019-03-19 22:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("experiments", "0033_auto_20190319_1820")]

    operations = [
        migrations.AddField(
            model_name="experiment",
            name="normandy_id",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="experiment",
            name="client_matching",
            field=models.TextField(
                blank=True, default="Prefs:\n\nStudies:\n\nAny additional filters:\n    "
            ),
        ),
    ]
