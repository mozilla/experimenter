import logging

from django.core.management.base import BaseCommand
from experimenter.experiments.constants import NO_FEATURE_SLUG

from experimenter.experiments.models import NimbusFeatureConfig
from experimenter.features import Features

logger = logging.getLogger()


class Command(BaseCommand):
    help = "Load Feature Configs from remote sources"

    def handle(self, *args, **options):
        logger.info("Loading Features")

        features_to_disable = set(
            NimbusFeatureConfig.objects.values_list("slug", flat=True)
        )

        for feature in Features.all():
            feature_config, created = NimbusFeatureConfig.objects.get_or_create(
                slug=feature.slug,
                application=feature.applicationSlug,
            )

            if not created:
                features_to_disable.discard(feature.slug)

            feature_config.name = feature.slug
            feature_config.description = feature.description
            feature_config.read_only = True
            feature_config.enabled = True

            if feature.variables is not None:
                feature_config.sets_prefs = [
                    v.setPref for v in feature.variables.values() if v.setPref is not None
                ]
            else:
                feature_config.sets_prefs = []

            if (schema := feature.get_jsonschema()) is not None:
                feature_config.schema = schema

            feature_config.save()
            logger.info(f"Feature Loaded: {feature.applicationSlug}/{feature.slug}")

        for feature_slug in features_to_disable:
            logger.info(f"Feature Not Found in YAML: {feature_slug}")
            if feature_slug not in NO_FEATURE_SLUG:
                feature_config = NimbusFeatureConfig.objects.get(slug=feature_slug)
                feature_config.enabled = False
                feature_config.save()

        logger.info("Features Updated")
