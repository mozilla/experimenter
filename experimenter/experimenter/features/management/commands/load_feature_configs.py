import logging

from django.core.management.base import BaseCommand

from experimenter.experiments.constants import NO_FEATURE_SLUG
from experimenter.experiments.models import (
    NimbusFeatureConfig,
    NimbusVersionedSchema,
)
from experimenter.features import Features

logger = logging.getLogger()


class Command(BaseCommand):
    help = "Load Feature Configs from remote sources"

    def handle(self, *args, **options):
        logger.info("Loading Features")

        features_to_disable = set(
            NimbusFeatureConfig.objects.values_list("application", "slug")
        )

        for feature in Features.all():
            feature_config, created = NimbusFeatureConfig.objects.update_or_create(
                slug=feature.slug,
                application=feature.application_slug,
                defaults={
                    "name": feature.slug,
                    "description": feature.model.description,
                    "enabled": True,
                },
            )

            if not created:
                features_to_disable.discard((feature.application_slug, feature.slug))

            defaults = {
                "sets_prefs": [
                    v.set_pref
                    for v in feature.model.variables.values()
                    if v.set_pref is not None
                ]
            }
            if (schema := feature.get_jsonschema()) is not None:
                defaults["schema"] = schema

            NimbusVersionedSchema.objects.update_or_create(
                feature_config=feature_config,
                version=None,
                defaults=defaults,
            )

            logger.info(f"Feature Loaded: {feature.application_slug}/{feature.slug}")

        for application_slug, feature_slug in features_to_disable:
            if feature_slug not in NO_FEATURE_SLUG:
                logger.info(f"Feature Not Found in YAML: {feature_slug}")
                feature_config = NimbusFeatureConfig.objects.filter(
                    application=application_slug, slug=feature_slug
                ).update(enabled=False)

        logger.info("Features Updated")
