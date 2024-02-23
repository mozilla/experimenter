import itertools
import logging
from typing import Optional, Union

from django.core.management.base import BaseCommand
from django.db import transaction
from mozilla_nimbus_schemas.experiments.feature_manifests import SetPref

from experimenter.experiments.constants import NO_FEATURE_SLUG, Application
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

    @transaction.atomic
    def handle(self, *args, **options):
        logger.info("Loading Features")

        # A mapping of (application slug, feature slug) to feature configs.
        #
        # Features will include multiples of the same feature, each with a
        # different version. We only need to create a single NimbusFeatureConfig
        # for each of those, so if we keep track of them we can skip a bunch of
        # update_or_create() calls.
        feature_configs: dict[tuple[str, str], NimbusFeatureConfig] = {
            (fc.application, fc.slug): fc for fc in NimbusFeatureConfig.objects.all()
        }

        features_to_disable = set(feature_configs.keys())

        # Iterate through the unversioned features first for the initial
        #
        # Then we can iterate over the versioned feature and create any that
        # aren't in the unversioned manifests.
        #
        # When we are ingesting versioned Features, we want to update the
        # NimbusFeatureConfig objects with the most up-to-date description.
        updated: set[tuple[str, str]] = set()
        for feature in itertools.chain(
            Features.unversioned(),
            sorted(Features.versioned(), key=lambda f: f.version, reverse=True),
        ):
            key = (feature.application_slug, feature.slug)
            if key in updated:
                # We have already processes the unversioned feature OR a
                # versioned feature at a newer version.
                #
                # The unversioned features are the most up-to-date (since they come from
                # the main branch (or equivalent)), so lets use the descriptions from
                # there, if they exist.
                continue

            feature_config = feature_configs.get(key)
            if feature_config is None:
                feature_config = feature_configs[key] = NimbusFeatureConfig(
                    slug=feature.slug,
                    application=feature.application_slug,
                    name=feature.slug,
                    description=feature.model.description,
                    # Only enable features from unversioned manifests.
                    enabled=feature.version is None,
                )

                # We don't have enough feature configs to justify moving this
                # into a bulk_create, as it does not noticably impact
                # performance.
                feature_config.save()
            else:
                # Django doesn't keep track of whether or not fields were updated
                # when you call save(). By default, it will update every field in
                # the object, whether or not it was dirtied. However, if we are
                # creating the object, we have to save every field anyway.
                dirty_fields = []

                if feature_config.name != feature.slug:
                    feature_config.name = feature.slug
                    dirty_fields.append("name")

                if feature_config.description != feature.model.description:
                    feature_config.description = feature.model.description
                    dirty_fields.append("description")

                # Only enable features from unversioned manifests.
                if not feature_config.enabled and feature.version is None:
                    feature_config.enabled = True
                    dirty_fields.append("enabled")

                if dirty_fields:
                    feature_config.save(update_fields=dirty_fields)

                if feature.version is None:
                    features_to_disable.remove(key)

            updated.add(key)

        # Disable any features that we didn't come across, except tombstone
        # features.
        for application_slug, feature_slug in features_to_disable:
            if feature_slug not in NO_FEATURE_SLUG:
                logger.info(f"Feature Not Found in YAML: {feature_slug}")
                feature_config = NimbusFeatureConfig.objects.filter(
                    application=application_slug, slug=feature_slug
                ).update(enabled=False)

        # Populate the version table and cache the results so we can re-use them
        # in NimbusVersionedSchema creation.
        versions: dict[Version, NimbusFeatureVersion] = {
            Version(v.major, v.minor, v.patch): v
            for v in NimbusFeatureVersion.objects.all()
        }

        versions_to_create = []
        for feature in Features.versioned():
            assert feature.version is not None

            if feature.version in versions:
                continue

            version = versions[feature.version] = NimbusFeatureVersion(
                major=feature.version.major,
                minor=feature.version.minor,
                patch=feature.version.patch,
            )
            versions_to_create.append(version)

        NimbusFeatureVersion.objects.bulk_create(versions_to_create)

        # A mapping of (feature_config.id, version.id) to NimbusVersionedSchemas.
        schemas: dict[tuple[int, Optional[int]], NimbusVersionedSchema] = {
            (schema.feature_config_id, schema.version_id): schema
            for schema in NimbusVersionedSchema.objects.all()
        }

        # If we call .save() on a newly created model, Django will not properly
        # aggregate all the model creations into a single operation. It is
        # faster to call save() only for updates and use bulk_create() for
        # inserts.
        schemas_to_create = []
        for feature in Features.all():
            feature_config = feature_configs[(feature.application_slug, feature.slug)]

            feature_version: Optional[NimbusFeatureVersion] = None
            feature_version_id: Optional[int] = None
            if feature.version:
                feature_version = versions[feature.version]
                feature_version_id = feature_version.id

            dirty_fields = []
            created = False

            schema = schemas.get((feature_config.id, feature_version_id))
            if schema is None:
                created = True
                schema = NimbusVersionedSchema(
                    feature_config=feature_config,
                    version=feature_version,
                    is_early_startup=feature.model.is_early_startup or False,
                    set_pref_vars={},
                )

            if (jsonschema := feature.get_jsonschema()) is not None:
                if schema.schema != jsonschema:
                    schema.schema = jsonschema
                    dirty_fields.append("schema")

            if feature_config.application == Application.DESKTOP:
                set_pref_vars = {
                    var_name: _set_pref_name(var.set_pref)
                    for var_name, var in feature.model.variables.items()
                    if var.set_pref is not None
                }

                if schema.set_pref_vars != set_pref_vars:
                    schema.set_pref_vars = set_pref_vars
                    dirty_fields.append("set_pref_vars")

                if (
                    feature.model.is_early_startup is not None
                    and schema.is_early_startup != feature.model.is_early_startup
                ):
                    schema.is_early_startup = feature.model.is_early_startup
                    dirty_fields.append("is_early_startup")

            if created:
                schemas_to_create.append(schema)
            elif dirty_fields:
                schema.save(update_fields=dirty_fields)

            logger.info(
                f"Feature Loaded: {feature.application_slug}/{feature.slug} "
                f"(version {feature.version})"
            )

        NimbusVersionedSchema.objects.bulk_create(schemas_to_create)

        logger.info("Features Updated")


def _set_pref_name(v: Union[SetPref, str]) -> str:
    if isinstance(v, SetPref):
        return v.pref
    else:
        return v
