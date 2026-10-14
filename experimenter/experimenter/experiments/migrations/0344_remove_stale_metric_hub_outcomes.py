from django.db import migrations
from django.db.models import Q

STALE_OUTCOME_SLUGS = (
    "pin-email-and-calendar-tabs-early-day-user",
    "pin-email-and-calendar-tabs-existing-user",
)


def remove_stale_outcomes(apps, schema_editor):
    NimbusExperiment = apps.get_model("experiments", "NimbusExperiment")

    experiments = NimbusExperiment.objects.filter(
        Q(primary_outcomes__overlap=STALE_OUTCOME_SLUGS)
        | Q(secondary_outcomes__overlap=STALE_OUTCOME_SLUGS)
    )

    for experiment in experiments:
        experiment.primary_outcomes = [
            slug
            for slug in experiment.primary_outcomes
            if slug not in STALE_OUTCOME_SLUGS
        ]
        experiment.secondary_outcomes = [
            slug
            for slug in experiment.secondary_outcomes
            if slug not in STALE_OUTCOME_SLUGS
        ]
        experiment.save(update_fields=["primary_outcomes", "secondary_outcomes"])


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0343_alter_nimbusalert_alert_type"),
    ]

    operations = [
        migrations.RunPython(remove_stale_outcomes, migrations.RunPython.noop),
    ]
