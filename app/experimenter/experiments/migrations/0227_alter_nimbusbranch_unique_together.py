# Generated by Django 3.2.16 on 2023-01-30 23:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0226_remove_viz_api_v1"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="nimbusbranch",
            unique_together={("slug", "experiment", "id")},
        ),
    ]
