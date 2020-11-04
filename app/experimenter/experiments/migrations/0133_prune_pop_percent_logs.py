from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0132_auto_20201103_1710"),
    ]

    def prune_new_changelog(apps, schema_editor):

        ExperimentChangeLog = apps.get_model("experiments", "ExperimentChangeLog")

        ExperimentChangeLog.objects.filter(
            message="Updated Population Percent", changed_values={}
        ).delete()

    operations = [
        migrations.RunPython(prune_new_changelog, reverse_code=migrations.RunPython.noop)
    ]
