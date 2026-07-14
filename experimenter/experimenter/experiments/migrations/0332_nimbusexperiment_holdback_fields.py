from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0331_alter_nimbusalert_alert_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="nimbusexperiment",
            name="is_holdback",
            field=models.BooleanField(
                default=False, verbose_name="Is Experiment a Holdback Flag"
            ),
        ),
        migrations.AddField(
            model_name="nimbusexperiment",
            name="do_rerun",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="nimbusexperiment",
            name="do_rerun_timestamp",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
