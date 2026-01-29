from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestFixIndonesianLanguageCodeMigration(MigratorTestCase):
    migrate_from = ("base", "0005_jajpmacos")
    migrate_to = ("base", "0006_fix_indonesian_language_code")

    def prepare(self):
        """Prepare test data before the migration."""
        Language = self.old_state.apps.get_model("base", "Language")

        # Create a Language with the incorrect "pk" code
        Language.objects.create(name="Indonesian", code="pk")

        # Create another language to ensure migration is targeted
        Language.objects.create(name="Polish", code="pl")

    def test_migration(self):
        Language = self.new_state.apps.get_model("base", "Language")

        # Check that Indonesian code was fixed
        indonesian = Language.objects.get(name="Indonesian")
        self.assertEqual(indonesian.code, "id")

        # Check that other languages were not affected
        polish = Language.objects.get(name="Polish")
        self.assertEqual(polish.code, "pl")
