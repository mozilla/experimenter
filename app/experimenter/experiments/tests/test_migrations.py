import random
import datetime

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test.testcases import TransactionTestCase

from experimenter.experiments.models import Experiment, ExperimentChangeLog
from experimenter.experiments.tests.factories import (
    ExperimentFactory,
    UserFactory,
    ExperimentVariantFactory,
)

from experimenter.experiments.constants import ExperimentConstants


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


class TestMigration(MigrationTestCase):

    migrate_from = [("experiments", "0071_auto_20190911_1515")]
    migrate_to = [("experiments", "0072_changelog_pruning")]

    def test_migration(self):

        exp1 = ExperimentFactory.create_with_status(
            target_status=ExperimentConstants.STATUS_DRAFT
        )

        exp2 = ExperimentFactory.create_with_status(
            target_status=ExperimentConstants.STATUS_LIVE
        )

        user1 = UserFactory()
        user2 = UserFactory()

        self.create_logs(exp1, user1)
        self.create_logs(exp1, user2)

        self.assertTrue(exp1.changes.count() > 11)
        self.assertEqual(exp2.changes.count(), 5)

        self.migrate_to_dest()

        exp1 = Experiment.objects.get(id=exp1.id)
        exp2 = Experiment.objects.get(id=exp2.id)
        self.assertEqual(exp1.changes.count(), 11)
        self.assertEqual(exp2.changes.count(), 5)

        #  1. Creation log
        self.assertEqual(
            ExperimentChangeLog.objects.filter(
                experiment=exp1,
                old_status=None,
                new_status=ExperimentConstants.STATUS_DRAFT,
            ).count(),
            1,
        )

        #  2. User1: first edit
        self.assertEqual(
            ExperimentChangeLog.objects.filter(
                experiment=exp1,
                old_status=ExperimentConstants.STATUS_DRAFT,
                new_status=ExperimentConstants.STATUS_DRAFT,
                changed_by=user1,
                changed_values={"description": "edit1"},
            ).count(),
            1,
        )

        #  3. User1: collasped dummy draft log
        self.assertEqual(
            ExperimentChangeLog.objects.filter(
                experiment=exp1,
                old_status=ExperimentConstants.STATUS_DRAFT,
                new_status=ExperimentConstants.STATUS_DRAFT,
                changed_by=user1,
                changed_values={},
            ).count(),
            1,
        )

        #  4. User1: draft -> review status change
        self.assertEqual(
            ExperimentChangeLog.objects.filter(
                experiment=exp1,
                old_status=ExperimentConstants.STATUS_DRAFT,
                new_status=ExperimentConstants.STATUS_REVIEW,
                changed_by=user1,
            ).count(),
            1,
        )

        # 5. User1 Edit Experiment review log
        self.assertEqual(
            ExperimentChangeLog.objects.filter(
                experiment=exp1,
                old_status=ExperimentConstants.STATUS_REVIEW,
                new_status=ExperimentConstants.STATUS_REVIEW,
                changed_by=user1,
                changed_values={"description": "edit2"},
            ).count(),
            1,
        )

        #  6. User2: first edit
        self.assertEqual(
            ExperimentChangeLog.objects.filter(
                experiment=exp1,
                old_status=ExperimentConstants.STATUS_DRAFT,
                new_status=ExperimentConstants.STATUS_DRAFT,
                changed_by=user2,
                changed_values={"description": "edit1"},
            ).count(),
            1,
        )

        #  7. User2: collasped dummy draft log
        self.assertEqual(
            ExperimentChangeLog.objects.filter(
                experiment=exp1,
                old_status=ExperimentConstants.STATUS_DRAFT,
                new_status=ExperimentConstants.STATUS_DRAFT,
                changed_by=user2,
                changed_values={},
            ).count(),
            1,
        )

        #  8. User2: draft -> review status change
        self.assertEqual(
            ExperimentChangeLog.objects.filter(
                experiment=exp1,
                old_status=ExperimentConstants.STATUS_DRAFT,
                new_status=ExperimentConstants.STATUS_REVIEW,
                changed_by=user2,
            ).count(),
            1,
        )

        # 9. User2 Edit Experiment review log
        self.assertEqual(
            ExperimentChangeLog.objects.filter(
                experiment=exp1,
                old_status=ExperimentConstants.STATUS_REVIEW,
                new_status=ExperimentConstants.STATUS_REVIEW,
                changed_by=user2,
                changed_values={"description": "edit2"},
            ).count(),
            1,
        )

        # 10 User1: collasped dummy review log
        self.assertEqual(
            ExperimentChangeLog.objects.filter(
                experiment=exp1,
                old_status=ExperimentConstants.STATUS_REVIEW,
                new_status=ExperimentConstants.STATUS_REVIEW,
                changed_by=user1,
                changed_values={},
            ).count(),
            1,
        )

        # 11 User2: collasped dummy review log
        self.assertEqual(
            ExperimentChangeLog.objects.filter(
                experiment=exp1,
                old_status=ExperimentConstants.STATUS_REVIEW,
                new_status=ExperimentConstants.STATUS_REVIEW,
                changed_by=user2,
                changed_values={},
            ).count(),
            1,
        )

    def create_logs(self, experiment, user):
        # changelog with changed values
        ExperimentChangeLog.objects.create(
            experiment=experiment,
            old_status=ExperimentConstants.STATUS_DRAFT,
            new_status=ExperimentConstants.STATUS_DRAFT,
            changed_on=datetime.datetime.now(),
            changed_by=user,
            changed_values={"description": "edit1"},
        )

        # generate no change changelogs for user
        self.create_dummy_changelogs(
            experiment, ExperimentConstants.STATUS_DRAFT, user, datetime.datetime.now()
        )

        # draft to review
        ExperimentChangeLog.objects.create(
            experiment=experiment,
            old_status=ExperimentConstants.STATUS_DRAFT,
            new_status=ExperimentConstants.STATUS_REVIEW,
            changed_on=datetime.datetime.now(),
            changed_by=user,
            changed_values=None,
        )

        # generate no change changelogs
        self.create_dummy_changelogs(
            experiment, ExperimentConstants.STATUS_REVIEW, user, datetime.datetime.now()
        )

        # changelog with changed values
        ExperimentChangeLog.objects.create(
            experiment=experiment,
            old_status=ExperimentConstants.STATUS_REVIEW,
            new_status=ExperimentConstants.STATUS_REVIEW,
            changed_on=datetime.datetime.now(),
            changed_by=user,
            changed_values={"description": "edit2"},
        )

        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)

        # generate no change changelogs
        self.create_dummy_changelogs(
            experiment, ExperimentConstants.STATUS_REVIEW, user, tomorrow
        )

    def create_dummy_changelogs(self, experiment, status, user, date):

        for i in range(random.randint(1, 8)):
            old_status = None if i % 2 == 0 else status

            ExperimentChangeLog.objects.create(
                experiment=experiment,
                old_status=old_status,
                new_status=status,
                changed_on=date,
                changed_by=user,
                changed_values={},
            )
