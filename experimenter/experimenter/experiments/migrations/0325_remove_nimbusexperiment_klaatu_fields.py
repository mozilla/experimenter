from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0324_nimbusexperiment_monitoring_data_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="nimbusexperiment",
            name="klaatu_status",
        ),
        migrations.RemoveField(
            model_name="nimbusexperiment",
            name="klaatu_recent_run_ids",
        ),
    ]
