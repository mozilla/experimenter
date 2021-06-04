from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test.testcases import TransactionTestCase


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


# Note: Here's a template for a data migration.  Copy this and fill it in with the
# relevant details for your data migration.  Also note that migration tests only
# work when the migration they're testing is the most recent one, so when a new
# migration is created you'll need to delete the tests.  This is fine though because
# the code is only run once at deploy time so after that the tests aren't needed.
#
# class TestMigrationExample(MigrationTestCase):

#     migrate_from = [("experiments", "0169_risk_questions_false")]
#     migrate_to = [("experiments", "0170_restore_feature_configs")]

#     def setUp(self):
#         super().setUp()
#         NimbusFeatureConfig.objects.all().delete()

#     def test_migration(self):
#         feature = NimbusFeatureConfigFactory.create()
#         experiment = NimbusExperimentFactory.create_with_lifecycle(
#             NimbusExperimentFactory.Lifecycles.CREATED,
#             feature_config=feature,
#         )

#         self.migrate_to_dest()

#         experiment = NimbusExperiment.objects.get(id=experiment.id)
#         self.assertEqual(experiment.feature_config, feature)
