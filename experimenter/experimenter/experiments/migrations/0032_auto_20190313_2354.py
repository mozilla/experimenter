# Generated by Django 2.1.7 on 2019-03-13 23:54

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("base", "0001_initial"),
        ("experiments", "0031_experiment_normandy_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="experiment",
            name="countries",
            field=models.ManyToManyField(to="base.Country"),
        ),
        migrations.AddField(
            model_name="experiment",
            name="locales",
            field=models.ManyToManyField(to="base.Locale"),
        ),
    ]
