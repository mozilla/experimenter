# Generated by Django 2.1.11 on 2019-08-23 21:31

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0066_remove_experiment_project"),
        ("projects", "0003_auto_20170630_1924"),
    ]

    operations = [migrations.DeleteModel(name="Project")]
