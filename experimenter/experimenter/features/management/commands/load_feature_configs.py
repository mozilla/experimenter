import itertools
import logging
from typing import Optional

from django.core.management.base import BaseCommand

from experimenter.experiments.constants import NO_FEATURE_SLUG
from experimenter.experiments.models import (
    NimbusFeatureConfig,
    NimbusFeatureVersion,
    NimbusVersionedSchema,
)
from experimenter.features import Features
from manifesttool.version import Version

logger = logging.getLogger()


class Command(BaseCommand):
    help = "Load Feature Configs from remote sources"

    def handle(self, *args, **options):
        logger.info("Loading Features")

        features_to_disable = set(
            NimbusFeatureConfig.objects.values_list("application", "slug")
        )

        # A mapping of (application slug, feature slug) to feature configs.
        #
        # Features will include multiples of the same feature, each with a
        # different version. We only need to create a single NimbusFeatureConfig
        # for each of those, so if we keep track of them we can skip a bunch of
        # update_or_create() calls.
        feature_configs: dict[tuple[str, str], NimbusFeatureConfig] = {}

        # Iterate through the unversioned features first for the initial
        # update_or_create() calls. The unversioned features are the most
        # up-to-date (since they come from the main branch (or equivalent)), so
        # lets use the descriptions from there.
        #
        # Then we can iterate over the versioned feature and create any that
        # aren't in the unversioned manifests.
        #
        # When we are ingesting versioned Features, we want to update the
        # NimbusFeatureConfig objects with the most up-to-date description.
        for feature in itertools.chain(
            Features.unversioned(),
            sorted(Features.versioned(), key=lambda f: f.version, reverse=True),
        ):
            if (feature.application_slug, feature.slug) in feature_configs:
                continue

            feature_config, created = NimbusFeatureConfig.objects.update_or_create(
                slug=feature.slug,
                application=feature.application_slug,
                defaults={
                    "name": feature.slug,
                    "description": feature.model.description,
                    "enabled": True,
                },
            )

            feature_configs[(feature.application_slug, feature.slug)] = feature_config

            if not created:
                features_to_disable.discard((feature.application_slug, feature.slug))

        # Disable any features that we didn't come across.
        for application_slug, feature_slug in features_to_disable:
            if feature_slug not in NO_FEATURE_SLUG:
                logger.info(f"Feature Not Found in YAML: {feature_slug}")
                feature_config = NimbusFeatureConfig.objects.filter(
                    application=application_slug, slug=feature_slug
                ).update(enabled=False)

        # Populate the version table and cache the results so we can re-use them
        # in model creation.
        versions: dict[Version, NimbusFeatureVersion] = {}
        for feature in Features.versioned():
            assert feature.version is not None

            if feature.version in versions:
                continue

            versions[feature.version] = NimbusFeatureVersion.objects.get_or_create(
                major=feature.version.major,
                minor=feature.version.minor,
                patch=feature.version.patch,
            )[0]

        for feature in Features.all():
            feature_config = feature_configs[(feature.application_slug, feature.slug)]
            feature_version: Optional[NimbusFeatureVersion] = None
            if feature.version:
                feature_version = versions[feature.version]

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
                version=feature_version,
                defaults=defaults,
            )

            logger.info(
                f"Feature Loaded: {feature.application_slug}/{feature.slug} "
                f"(version {feature.version})"
            )

        logger.info("Features Updated")
