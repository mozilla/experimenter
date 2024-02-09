from unittest import mock

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase


class TestDocs(TestCase):
    def test_generate_docs(self):

        docs_dir = settings.BASE_DIR / "docs"
        schema_json_path = docs_dir / "openapi-schema.json"
        swagger_html_path = docs_dir / "swagger-ui.html"

        with mock.patch(
            "experimenter.base.management.commands.generate_docs.Path.open",
            mock.mock_open(read_data="{}"),
        ) as mf:

            call_command("generate_docs")

            self.assertEqual(mf.call_count, 2)
            mf.assert_any_call(swagger_html_path, "w+")
            mf.assert_any_call(schema_json_path, "w+")

    def test_check_docs_returns_with_diff_jsons(self):

        with mock.patch(
            "experimenter.base.management.commands.generate_docs.Path.open",
            mock.mock_open(read_data="{}"),
        ), self.assertRaises(ValueError) as cm:
            call_command("generate_docs", "--check=true")
            self.assertIn("Api Schemas have changed and have not been updated", cm.value)
