# Generated by Django 2.1.2 on 2019-01-03 18:49

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("experiments", "0021_auto_20181030_1805")]

    operations = [
        migrations.RemoveField(model_name="experiment", name="review_phd"),
        migrations.AlterField(
            model_name="experiment",
            name="status",
            field=models.CharField(
                choices=[
                    ("Draft", "Draft"),
                    ("Review", "Ready for Sign-Off"),
                    ("Ship", "Ready to Ship"),
                    ("Accepted", "Accepted by Shield"),
                    ("Live", "Live"),
                    ("Complete", "Complete"),
                    ("Rejected", "Rejected"),
                ],
                default="Draft",
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="experimentchangelog",
            name="new_status",
            field=models.CharField(
                choices=[
                    ("Draft", "Draft"),
                    ("Review", "Ready for Sign-Off"),
                    ("Ship", "Ready to Ship"),
                    ("Accepted", "Accepted by Shield"),
                    ("Live", "Live"),
                    ("Complete", "Complete"),
                    ("Rejected", "Rejected"),
                ],
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="experimentchangelog",
            name="old_status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("Draft", "Draft"),
                    ("Review", "Ready for Sign-Off"),
                    ("Ship", "Ready to Ship"),
                    ("Accepted", "Accepted by Shield"),
                    ("Live", "Live"),
                    ("Complete", "Complete"),
                    ("Rejected", "Rejected"),
                ],
                max_length=255,
                null=True,
            ),
        ),
    ]
