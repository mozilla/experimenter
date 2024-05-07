# Generated by Django 5.0.3 on 2024-05-07 22:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0268_remove_ios_nightly"),
    ]

    operations = [
        migrations.AddField(
            model_name="nimbusexperiment",
            name="conclusion_recommendations",
            field=models.JSONField(
                blank=True,
                default=list,
                null=True,
                verbose_name="Conclusion Recommendations",
            ),
        ),
    ]
