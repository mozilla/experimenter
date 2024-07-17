from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestMigrations(MigratorTestCase):
    migrate_from = (
        "base",
        "0004_language",
    )
    migrate_to = (
        "base",
        "0005_jajpmacos",
    )

    def prepare(self):
        """Prepare some data before the migration."""
        Locale = self.old_state.apps.get_model("base", "Locale")

        Locale.objects.create(code="ja-JP-mac", name="Japanese")

    def test_migration(self):
        """Run the test itself."""
        Locale = self.new_state.apps.get_model("base", "Locale")

        self.assertFalse(Locale.objects.filter(code="ja-JP-mac").exists())

        locale = Locale.objects.get(code="ja-JP-macos")

        self.assertEqual(locale.name, "Japanese (macOS)")
