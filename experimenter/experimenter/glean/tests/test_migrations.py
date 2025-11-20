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
