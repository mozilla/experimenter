from collections import defaultdict

import django.contrib.postgres.fields.jsonb
import django.core.serializers.json
from django.db import migrations
from django.db.models import F

from experimenter.legacy.legacy_experiments.constants import ExperimentConstants


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
        for experiment in Experiment.objects.all():
            changes = experiment.changes.filter(
                changed_values={}, old_status=F("new_status")
            ).order_by("changed_on")
            seen_edits = set()
            current_date = None
            for change in changes:
                if change.changed_on.date() != current_date:
                    seen_edits = set([change.changed_by.email])
                    current_date = change.changed_on.date()
                elif change.changed_by.email in seen_edits:
                    change.delete()
                else:
                    seen_edits.add(change.changed_by.email)

    operations = [
        migrations.RunPython(prune_new_changelog, reverse_code=migrations.RunPython.noop)
    ]
