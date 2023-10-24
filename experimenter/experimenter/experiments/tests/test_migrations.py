import json
from itertools import product

from django_test_migrations.contrib.unittest_case import MigratorTestCase
from faker import Faker

from experimenter.experiments.constants import NimbusConstants


class TestRemoveDirtyPublishStatusMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0248_alter_nimbusexperiment_channel",
    )
    migrate_to = (
        "experiments",
        "0249_alter_nimbusbranchfeaturevalue_feature_config",
    )

    def prepare(self):
        """Prepare some data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        NimbusFeatureConfig = self.old_state.apps.get_model(
            "experiments", "NimbusFeatureConfig"
        )
        NimbusExperiment = self.old_state.apps.get_model(
            "experiments", "NimbusExperiment"
        )
        NimbusBranch = self.old_state.apps.get_model("experiments", "NimbusBranch")
        NimbusBranchFeatureValue = self.old_state.apps.get_model(
            "experiments", "NimbusBranchFeatureValue"
        )
        user = User.objects.create(email="test@example.com")

        feature_config = NimbusFeatureConfig.objects.create(
            slug="test-feature", application=NimbusConstants.Application.DESKTOP
        )
        experiment = NimbusExperiment.objects.create(
            owner=user,
            name="test experiment",
            slug="test-experiment",
            application=NimbusConstants.Application.DESKTOP,
            status=NimbusConstants.Status.DRAFT,
            publish_status=NimbusConstants.PublishStatus.IDLE,
            published_dto="{}",
        )
        experiment.feature_configs.add(feature_config)
        branch = NimbusBranch.objects.create(
            experiment=experiment,
            name="test branch",
            slug="test-branch",
        )
        NimbusBranchFeatureValue.objects.create(
            branch=branch, feature_config=None, value="{}"
        )
        NimbusBranchFeatureValue.objects.create(
            branch=branch, feature_config=feature_config, value="{}"
        )

    def test_migration(self):
        """Run the test itself."""
        NimbusFeatureConfig = self.new_state.apps.get_model(
            "experiments", "NimbusFeatureConfig"
        )
        NimbusBranchFeatureValue = self.new_state.apps.get_model(
            "experiments", "NimbusBranchFeatureValue"
        )
        feature_config = NimbusFeatureConfig.objects.get(slug="test-feature")

        self.assertEqual(
            NimbusBranchFeatureValue.objects.filter(feature_config=None).count(), 0
        )
        self.assertEqual(
            NimbusBranchFeatureValue.objects.filter(
                feature_config=feature_config
            ).count(),
            1,
        )


class TestNimbusVersionedFeatureConfigMigration(MigratorTestCase):
    migrate_from = (
        "experiments",
        "0239_alter_nimbusexperiment_experiment_targeting_blank",
    )
    migrate_to = ("experiments", "0240_nimbusversionedschema")

    JSON_SCHEMA = json.dumps(
        {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "variable": {"description": "variable description", "type": "string"}
            },
            "additionalProperties": False,
        }
    )

    def prepare(self):
        fake = Faker()

        self.instances = [
            {
                "slug": fake.slug(),
                "name": fake.slug(),
                "description": fake.text(),
                "owner_email": fake.email(),
                "application": application,
                "sets_prefs": sets_prefs,
                "read_only": read_only,
                "schema": self.JSON_SCHEMA,
                "enabled": enabled,
            }
            for (application, sets_prefs, read_only, enabled) in (
                product(
                    list(NimbusConstants.Application),
                    ([], [fake.slug().replace("-", ".")]),
                    (True, False),
                    (True, False),
                )
            )
        ]

        NimbusFeatureConfig = self.old_state.apps.get_model(
            "experiments", "NimbusFeatureConfig"
        )
        NimbusFeatureConfig.objects.bulk_create(
            NimbusFeatureConfig(**kwargs) for kwargs in self.instances
        )

    def test_migration(self):
        NimbusFeatureConfig = self.new_state.apps.get_model(
            "experiments", "NimbusFeatureConfig"
        )
        NimbusVersionedSchema = self.new_state.apps.get_model(
            "experiments", "NimbusVersionedSchema"
        )

        by_slug = {
            fc.slug: fc
            for fc in NimbusFeatureConfig.objects.all().prefetch_related("schemas")
        }

        for kwargs in self.instances:
            feature_config = by_slug[kwargs["slug"]]

            self.assertEqual(feature_config.description, kwargs["description"])
            self.assertEqual(feature_config.enabled, kwargs["enabled"])
            self.assertEqual(feature_config.name, kwargs["name"])
            self.assertEqual(feature_config.owner_email, kwargs["owner_email"])

            versioned_schemas = list(feature_config.schemas.all())
            self.assertEqual(len(versioned_schemas), 1)

            versioned_schema = versioned_schemas[0]

            self.assertEqual(versioned_schema.schema, self.JSON_SCHEMA)
            self.assertEqual(versioned_schema.sets_prefs, kwargs["sets_prefs"])
            self.assertEqual(versioned_schema.version, None)

        self.assertEqual(
            NimbusVersionedSchema.objects.count(),
            len(by_slug),
            (
                "There should be an equal number of NimbusVersionedSchemas and "
                "NimbusFeatureConfigs",
            ),
        )
