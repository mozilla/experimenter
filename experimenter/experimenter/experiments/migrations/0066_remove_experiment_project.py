# Generated by Django 2.1.11 on 2019-08-23 21:31

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("experiments", "0065_results_section")]

    operations = [migrations.RemoveField(model_name="experiment", name="project")]
