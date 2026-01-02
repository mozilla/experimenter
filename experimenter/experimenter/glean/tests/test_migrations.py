from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestMigrations(MigratorTestCase):
    migrate_from = ("glean", "0001_initial")
    migrate_to = ("glean", "0002_glean_dismiss_reset")

    def prepare(self):
        """Prepare test data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        Prefs = self.old_state.apps.get_model("glean", "Prefs")

        user = User.objects.create_user(username="testuser", password="testpass")
        Prefs.objects.create(user=user, alert_dismissed=True, opt_out=False)

    def test_migration(self):
        Prefs = self.new_state.apps.get_model("glean", "Prefs")
        prefs = Prefs.objects.get(user__username="testuser")
        self.assertFalse(prefs.alert_dismissed)


class TestPrefsNimbusUserIDMigration(MigratorTestCase):
    migrate_from = ("glean", "0002_glean_dismiss_reset")
    migrate_to = ("glean", "0003_prefs_nimbus_user_id")

    def prepare(self):
        """Prepare test data before the migration."""
        User = self.old_state.apps.get_model("auth", "User")
        Prefs = self.old_state.apps.get_model("glean", "Prefs")

        user1 = User.objects.create_user(username="testuser1", password="testpass")
        Prefs.objects.create(user=user1, alert_dismissed=True, opt_out=False)

        user2 = User.objects.create_user(username="testuser2", password="testpass")
        Prefs.objects.create(user=user2, alert_dismissed=True, opt_out=True)

    def test_migration(self):
        Prefs = self.new_state.apps.get_model("glean", "Prefs")

        prefs1 = Prefs.objects.get(user__username="testuser1")
        self.assertIsNotNone(prefs1.nimbus_user_id)

        prefs2 = Prefs.objects.get(user__username="testuser2")
        self.assertIsNone(prefs2.nimbus_user_id)
