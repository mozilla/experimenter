# Generated by Django 2.1.7 on 2019-03-07 16:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0001_initial"),
        ("experiments", "0029_auto_20190206_2028"),
    ]

    operations = [
        migrations.AddField(
            model_name="experiment",
            name="all_countries",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="experiment",
            name="all_locales",
            field=models.BooleanField(default=False),
        ),
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
