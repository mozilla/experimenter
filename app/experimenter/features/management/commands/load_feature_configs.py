import logging

from django.core.management.base import BaseCommand

from experimenter.experiments.models import NimbusFeatureConfig
from experimenter.features import Features

logger = logging.getLogger()


class Command(BaseCommand):
    help = "Load Feature Configs from remote sources"

    def handle(self, *args, **options):
        logger.info("Loading Features")

        for feature in Features.all():
            feature_config, _ = NimbusFeatureConfig.objects.get_or_create(
                name=feature.slug,
                slug=feature.slug,
                application=feature.applicationSlug,
            )
            feature_config.description = feature.description
            feature_config.schema = feature.schema
            feature_config.read_only = True
            feature_config.save()
            logger.info(f"Feature Loaded: {feature.applicationSlug}/{feature.slug}")

        logger.info("Features Updated")
