# Generated by Django 3.2.5 on 2021-11-02 17:49

from django.db import migrations


def set_feature_value(apps, schema_editor):
    NimbusBranch = apps.get_model("experiments", "NimbusBranch")
    NimbusBranch.objects.filter(feature_value="").update(feature_value="{}")


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0193_remove_nimbusbranch_feature_enabled"),
    ]

    operations = [
        migrations.RunPython(set_feature_value),
    ]
