"""
from django.conf import settings
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test.testcases import TransactionTestCase


class MigrationTestCase(TransactionTestCase):
    A Test case for testing migrations

    migrate_from = None
    migrate_to = None

    def setUp(self):
        super(MigrationTestCase, self).setUp()

        self.executor = MigrationExecutor(connection)
        self.executor.migrate(self.migrate_from)
        self.old_apps = self.executor.loader.project_state(self.migrate_from).apps
        self.new_apps = self.executor.loader.project_state(self.migrate_to).apps

    def migrate_to_dest(self):
        self.executor.loader.build_graph()  # reload.
        self.executor.migrate(self.migrate_to)


class TestMigration0073(MigrationTestCase):

    migrate_from = [("experiments", "0072_changelog_pruning")]
    migrate_to = [("experiments", "0073_experiment_new_analysis_owner")]

    def test_migration(self):
        OldUser = self.old_apps.get_model(*settings.AUTH_USER_MODEL.split("."))
        OldExperiment = self.old_apps.get_model("experiments", "Experiment")

        jdata = "jdata@example.com"
        jdota = "jdota@example.com"

        user_jdata = OldUser.objects.create(username=jdata, email=jdata)
        OldUser.objects.create(username=jdota, email=jdota)
        OldUser.objects.create(username="duplicate jdota", email=jdota)
        experiment = OldExperiment.objects.create(
            name="Beep", slug="beep", analysis_owner="Jim Data"
        )

        OldExperiment.objects.create(name="Boop", slug="boop", analysis_owner=None)

        self.migrate_to_dest()

        NewUser = self.new_apps.get_model(*settings.AUTH_USER_MODEL.split("."))
        NewExperiment = self.new_apps.get_model("experiments", "Experiment")

        user_jdata = NewUser.objects.get(email=jdata)
        experiment = NewExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.analysis_owner, user_jdata)
"""
