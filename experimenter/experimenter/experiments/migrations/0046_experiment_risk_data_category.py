# Generated by Django 2.1.7 on 2019-04-18 22:01

from django.db import migrations, models

from experimenter.legacy.legacy_experiments.constants import ExperimentConstants


def populate_new_risk_fields(apps, schema_editor):
    Experiment = apps.get_model("experiments", "Experiment")
    filtered_experiments = Experiment.objects.filter(
        status__in=[
            ExperimentConstants.STATUS_SHIP,
            ExperimentConstants.STATUS_ACCEPTED,
            ExperimentConstants.STATUS_LIVE,
            ExperimentConstants.STATUS_COMPLETE,
            "Rejected",
        ]
    )
    for risk in all_risks():
        filtered_experiments.filter(**{risk: None}).update(**{risk: False})


def all_risks():
    return (
        "risk_internal_only",
        "risk_partner_related",
        "risk_brand",
        "risk_fast_shipped",
        "risk_confidential",
        "risk_release_population",
        "risk_data_category",
        "risk_technical",
    )


class Migration(migrations.Migration):
    dependencies = [("experiments", "0045_auto_20190408_2059")]

    operations = [
        migrations.AddField(
            model_name="experiment",
            name="risk_data_category",
            field=models.NullBooleanField(default=None),
        ),
        migrations.RunPython(populate_new_risk_fields),
    ]
