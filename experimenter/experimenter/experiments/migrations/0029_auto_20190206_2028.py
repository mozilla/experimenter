# Generated by Django 2.1.2 on 2019-02-06 20:28

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("experiments", "0028_auto_20190201_1820")]

    operations = [
        migrations.AlterField(
            model_name="experiment",
            name="risks",
            field=models.TextField(blank=True, null=True),
        )
    ]
