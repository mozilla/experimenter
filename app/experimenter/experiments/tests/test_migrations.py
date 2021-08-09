from django.contrib.auth.models import User
from django_test_migrations.contrib.unittest_case import MigratorTestCase

from experimenter.experiments.tests.factories import (
    ExperimentChangeLogFactory,
    ExperimentCommentFactory,
    ExperimentFactory,
    NimbusChangeLogFactory,
    NimbusExperimentFactory,
)
from experimenter.notifications.tests.factories import NotificationFactory
from experimenter.openidc.tests.factories import UserFactory


class TestMigration0181Forward(MigratorTestCase):
    migrate_from = ("experiments", "0180_auto_20210803_1832")
    migrate_to = ("experiments", "0181_remove_non_ldap_emails")

    def prepare(self):
        """Prepare some data before the migration."""
        self.preserve_users = [
            ExperimentChangeLogFactory.create().changed_by,
            ExperimentCommentFactory.create().created_by,
            ExperimentFactory.create().analysis_owner,
            ExperimentFactory.create().owner,
            NimbusChangeLogFactory.create().changed_by,
            NimbusExperimentFactory.create().owner,
            NotificationFactory.create().user,
            UserFactory.create(email="person@mozilla.com"),
            UserFactory.create(email="person@getpocket.com"),
        ]
        self.delete_users = [
            UserFactory.create(email="person@example.com"),
        ]

    def test_migration(self):
        """Run the test itself."""
        for preserved_user in self.preserve_users:
            self.assertTrue(User.objects.filter(id=preserved_user.id).exists())

        for deleted_user in self.delete_users:
            self.assertFalse(User.objects.filter(id=deleted_user.id).exists())
