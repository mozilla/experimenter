from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test.testcases import TransactionTestCase

from experimenter.experiments.models import ExperimentChangeLog
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.openidc.tests.factories import UserFactory


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


class TestMigrationVersion(MigrationTestCase):

    migrate_from = [("experiments", "0121_prune_add_version_changelogs")]
    migrate_to = [("experiments", "0122_prune_all_add_version_changelogs")]

    def test_migration(self):

        experiment = ExperimentFactory.create()
        user = UserFactory.create()

        ExperimentChangeLog.objects.create(
            experiment=experiment,
            message="Something Else",
            changed_by=user,
        )

        ExperimentChangeLog.objects.create(
            experiment=experiment,
            message="Added Version(s)",
            changed_by=user,
        )

        ExperimentChangeLog.objects.create(
            experiment=experiment,
            message="Added Version(s)",
            changed_by=user,
            changed_values={
                "firefox_max_version": {
                    "old_value": "79.0",
                    "new_value": "80.0",
                    "display_name": "Firefox Max Version",
                }
            },
        )

        self.migrate_to_dest()

        self.assertEqual(ExperimentChangeLog.objects.count(), 1)
        self.assertTrue(
            ExperimentChangeLog.objects.filter(message="Something Else").exists()
        )


class TestMigrationPercent(MigrationTestCase):

    migrate_from = [("experiments", "0132_auto_20201103_1710")]
    migrate_to = [("experiments", "0133_prune_pop_percent_logs")]

    def test_migration(self):

        experiment = ExperimentFactory.create()
        user = UserFactory.create()

        ExperimentChangeLog.objects.create(
            experiment=experiment,
            message="Something Else",
            changed_by=user,
        )

        ExperimentChangeLog.objects.create(
            experiment=experiment,
            message="Updated Population Percent",
            changed_by=user,
            changed_values={},
        )

        ExperimentChangeLog.objects.create(
            experiment=experiment,
            message="Updated Population Percent",
            changed_by=user,
            changed_values={
                "population_percent": {
                    "old_value": "2.0000",
                    "new_value": "3.0000",
                    "display_name": "Population Percent",
                }
            },
        )

        self.migrate_to_dest()

        self.assertEqual(ExperimentChangeLog.objects.count(), 2)
        self.assertTrue(
            ExperimentChangeLog.objects.filter(message="Something Else").exists()
        )
        self.assertTrue(
            ExperimentChangeLog.objects.filter(
                message="Updated Population Percent",
                changed_values={
                    "population_percent": {
                        "old_value": "2.0000",
                        "new_value": "3.0000",
                        "display_name": "Population Percent",
                    }
                },
            ).exists()
        )
