# Generated by Django 2.1.10 on 2019-07-19 19:25

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("experiments", "0063_auto_20190730_0225")]

    operations = [
        migrations.AddField(
            model_name="experiment",
            name="other_normandy_ids",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.IntegerField(), blank=True, null=True, size=None
            ),
        )
    ]
