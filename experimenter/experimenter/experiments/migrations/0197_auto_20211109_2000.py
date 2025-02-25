# Generated by Django 3.2.5 on 2021-11-09 20:00

from decimal import Decimal

from django.db import migrations


def restore_bucket_range(apps, schema_editor):
    NimbusExperiment = apps.get_model("experiments", "NimbusExperiment")
    NimbusIsolationGroup = apps.get_model("experiments", "NimbusIsolationGroup")
    NimbusBucketRange = apps.get_model("experiments", "NimbusBucketRange")

    # The set of experiments that may have been affected are those with both
    # an allocated bucket range and a published_dto
    for experiment in NimbusExperiment.objects.exclude(bucket_range=None).exclude(
        published_dto=None
    ):
        # The namespace that is currently stored in the database
        db_namespace = "-".join(
            [
                experiment.bucket_range.isolation_group.name,
                str(experiment.bucket_range.isolation_group.instance),
            ]
        )

        # The namespace that appears in the published_dto
        published_namespace = experiment.published_dto.get("bucketConfig", {}).get(
            "namespace"
        )

        # If the published and stored namespace differs then the bucket range
        # has been erroneously regenerated and we need to restore it back to the
        # published values
        if published_namespace and published_namespace != db_namespace:
            split_namespace = published_namespace.split("-")
            published_namespace_name = ("-").join(split_namespace[:-1])
            published_namespace_instance = int(split_namespace[-1])

            # The original namespace may still exist or it may have been deleted if
            # the bucket range was regenerated and it contained only a single bucket range
            (
                original_isolation_group,
                created,
            ) = NimbusIsolationGroup.objects.get_or_create(
                application=experiment.application,
                name=published_namespace_name,
                instance=published_namespace_instance,
                total=10000,  # Hard coded here to prevent unintended import chains
            )

            # We can safely delete the erroneously regenerated bucket range
            NimbusBucketRange.objects.filter(experiment=experiment).delete()

            # We can create a new bucket range with the values from the published_dto
            NimbusBucketRange.objects.create(
                experiment=experiment,
                isolation_group=original_isolation_group,
                start=experiment.published_dto.get("bucketConfig", {}).get("start", 0),
                count=experiment.published_dto.get("bucketConfig", {}).get(
                    "count",
                    int(
                        experiment.population_percent
                        / Decimal("100.0")
                        * NimbusExperiment.BUCKET_TOTAL
                    ),
                ),
            )


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0196_nimbusbranch_feature_enabled"),
    ]

    operations = [
        migrations.RunPython(restore_bucket_range),
    ]
