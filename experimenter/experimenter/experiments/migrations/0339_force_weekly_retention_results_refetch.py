from django.db import migrations

BATCH_SIZE = 100


def stored_analysis_start_time(results_data):
    metadata = (results_data.get("v3") or {}).get("metadata")
    return metadata.get("analysis_start_time") if isinstance(metadata, dict) else None


def force_results_refetch(apps, schema_editor):
    NimbusExperiment = apps.get_model("experiments", "NimbusExperiment")

    stale_experiments = []
    for experiment in NimbusExperiment.objects.exclude(results_data=None).iterator(
        chunk_size=BATCH_SIZE
    ):
        if stored_analysis_start_time(experiment.results_data) is None:
            continue

        experiment.results_data["v3"]["metadata"]["analysis_start_time"] = None
        stale_experiments.append(experiment)

        if len(stale_experiments) == BATCH_SIZE:
            NimbusExperiment.objects.bulk_update(stale_experiments, ["results_data"])
            stale_experiments.clear()

    NimbusExperiment.objects.bulk_update(stale_experiments, ["results_data"])


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0338_nimbusemail_rollout_phase_alter_nimbusemail_type"),
    ]

    operations = [
        migrations.RunPython(force_results_refetch, migrations.RunPython.noop),
    ]
