import parameterized
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test.testcases import TransactionTestCase

from experimenter.experiments.changelog_utils.nimbus import generate_nimbus_changelog
from experimenter.experiments.models import NimbusExperiment, NimbusFeatureConfig
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)


class MigrationTestCase(TransactionTestCase):
    """A Test case for testing migrations"""

    migrate_from = None
    migrate_to = None

    def setUp(self):
        super(MigrationTestCase, self).setUp()

        self.executor = MigrationExecutor(connection)
        self.executor.migrate(self.migrate_from)

    def migrate_to_dest(self):
        self.executor.loader.build_graph()  # reload.
        self.executor.migrate(self.migrate_to)


@parameterized.parameterized_class(
    ("feature_config_slug",),
    (("no-feature-firefox-desktop",), ("no-feature-fenix",), ("no-feature-ios",)),
)
class TestMigration0170(MigrationTestCase):

    migrate_from = [("experiments", "0169_risk_questions_false")]
    migrate_to = [("experiments", "0170_restore_feature_configs")]

    def setUp(self):
        super().setUp()
        NimbusFeatureConfig.objects.all().delete()

    def test_migration_restore_original_feature(self):
        original_feature = NimbusFeatureConfigFactory.create()
        incorrect_feature = NimbusFeatureConfigFactory.create(
            slug=self.feature_config_slug
        )

        # Experiment was created with no feature when features weren't required
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
            feature_config=None,
            application=NimbusExperiment.Application.DESKTOP,
        )
        generate_nimbus_changelog(experiment, experiment.owner, "feature is None")

        # Desired feature is set by owner
        experiment.feature_config = original_feature
        experiment.save()
        generate_nimbus_changelog(experiment, experiment.owner, "set original feature")

        # Oops unset the original_feature config in migration 166
        experiment.feature_config = incorrect_feature
        experiment.save()

        # A changelog may have occurred after the migration
        generate_nimbus_changelog(experiment, experiment.owner, "set incorrect feature")

        self.migrate_to_dest()

        # Experiment is restored to original feature
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.feature_config, original_feature)

    def test_migration_feature_only_set_by_166(self):
        default_feature = NimbusFeatureConfigFactory.create(slug=self.feature_config_slug)

        # Experiment was created with no feature when features weren't required
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
            feature_config=None,
            application=NimbusExperiment.Application.DESKTOP,
        )
        generate_nimbus_changelog(experiment, experiment.owner, "feature is None")

        # Default feature is set by 166 but no changelog is created
        experiment.feature_config = default_feature
        experiment.save()

        self.migrate_to_dest()

        # Experiment remains on default feature
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.feature_config, default_feature)

    def test_migration_uses_latest_feature_config_not_default(self):
        original_feature = NimbusFeatureConfigFactory.create()
        intermediate_feature = NimbusFeatureConfigFactory.create()
        incorrect_feature = NimbusFeatureConfigFactory.create(
            slug=self.feature_config_slug
        )

        # Experiment was created with no feature when features weren't required
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperiment.Lifecycles.CREATED,
            feature_config=None,
        )
        generate_nimbus_changelog(experiment, experiment.owner, "feature is None")

        # Intermediate feature is set by owner
        experiment.feature_config = intermediate_feature
        experiment.save()
        generate_nimbus_changelog(experiment, experiment.owner, "set original feature")

        # Desired feature is set by owner
        experiment.feature_config = original_feature
        experiment.save()
        generate_nimbus_changelog(experiment, experiment.owner, "set original feature")

        # Oops unset the original_feature config in migration 166
        experiment.feature_config = incorrect_feature
        experiment.save()

        # A changelog may have occurred after the migration
        generate_nimbus_changelog(experiment, experiment.owner, "set incorrect feature")

        self.migrate_to_dest()

        # Experiment is restored to original feature
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.feature_config, original_feature)
