# Generated by Django 2.1.7 on 2019-04-08 20:17

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("experiments", "0043_auto_20190404_2015")]

    operations = [migrations.RemoveField(model_name="experiment", name="addon_name")]
