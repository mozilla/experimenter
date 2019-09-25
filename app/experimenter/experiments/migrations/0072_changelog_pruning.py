import django.contrib.postgres.fields.jsonb
import django.core.serializers.json
from django.db import migrations
from django.db.models import F
from experimenter.experiments.constants import ExperimentConstants


class Migration(migrations.Migration):

    dependencies = [("experiments", "0071_auto_20190911_1515")]

    def prune_new_changelog(apps, schema_editor):
        ExperimentChangeLog = apps.get_model("experiments", "ExperimentChangeLog")

        Experiment = apps.get_model("experiments", "experiment")

        for experiment in Experiment.objects.all():
            change_logs = experiment.changes.filter(old_status=None).order_by(
                "changed_on"
            )[1:]
            for log in change_logs:
                log.old_status = log.new_status
                log.save()

        # prune changelogs that describe no change
        ExperimentChangeLog.objects.filter(
            changed_values={}, old_status=F("new_status")
        ).delete()

    operations = [migrations.RunPython(prune_new_changelog)]
