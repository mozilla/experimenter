# Generated by Django 2.1.2 on 2019-01-07 22:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("experiments", "0024_auto_20190107_2049")]

    operations = [
        migrations.AddField(
            model_name="experiment",
            name="review_intent_to_ship",
            field=models.NullBooleanField(default=None),
        ),
        migrations.AddField(
            model_name="experiment",
            name="review_qa_requested",
            field=models.NullBooleanField(default=None),
        ),
        migrations.AlterField(
            model_name="experiment",
            name="type",
            field=models.CharField(
                choices=[("pref", "Pref-Flip Study"), ("addon", "Add-On Study")],
                default="pref",
                max_length=255,
            ),
        ),
    ]
