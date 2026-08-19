import json
from io import StringIO

from django.core.management import call_command
from django.test import TestCase


class TestExportTargetingSql(TestCase):
    def test_outputs_valid_json(self):
        out = StringIO()
        call_command("export_targeting_sql", stdout=out)
        entries = json.loads(out.getvalue())
        self.assertIsInstance(entries, list)

    def test_entries_have_slug_and_query(self):
        out = StringIO()
        call_command("export_targeting_sql", stdout=out)
        entries = json.loads(out.getvalue())
        self.assertTrue(len(entries) > 0)
        for entry in entries:
            self.assertIn("slug", entry)
            self.assertIn("query", entry)

    def test_queries_use_where_false(self):
        out = StringIO()
        call_command("export_targeting_sql", stdout=out)
        entries = json.loads(out.getvalue())
        for entry in entries:
            self.assertIn("WHERE FALSE", entry["query"])

    def test_queries_use_countif(self):
        out = StringIO()
        call_command("export_targeting_sql", stdout=out)
        entries = json.loads(out.getvalue())
        for entry in entries:
            self.assertIn("SELECT COUNTIF(", entry["query"])

    def test_only_desktop_configs_included(self):
        out = StringIO()
        call_command("export_targeting_sql", stdout=out)
        entries = json.loads(out.getvalue())
        # Mobile-only slugs should not appear
        slugs = {e["slug"] for e in entries}
        self.assertNotIn("no_targeting", slugs)
