# Generated by Django 3.2.12 on 2022-05-02 16:08

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("base", "0003_siteflag"),
    ]

    operations = [
        migrations.CreateModel(
            name="Language",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.CharField(max_length=255, unique=True)),
                ("name", models.CharField(max_length=255)),
            ],
            options={
                "verbose_name": "Language",
                "verbose_name_plural": "Languages",
                "ordering": ("name",),
            },
        ),
    ]
