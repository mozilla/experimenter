from unittest import mock

from django.core.management import call_command
from django.test import TestCase


class TestDocs(TestCase):
    @mock.patch(
        "experimenter.base.management.commands.generate_docs.settings.SCHEMA_JSON_PATH"
    )
    @mock.patch(
        "experimenter.base.management.commands.generate_docs.settings.SWAGGER_HTML_PATH"
    )
    def test_generate_docs(self, mock_schema_json_path, mock_swagger_html_path):
        call_command("generate_docs")

        mock_schema_json_path.open.assert_any_call("w+")
        mock_swagger_html_path.open.assert_any_call("w+")

    @mock.patch(
        "experimenter.base.management.commands.generate_docs.settings.SCHEMA_JSON_PATH",
    )
    def test_check_docs_returns_with_diff_jsons(self, mock_schema_json_path):
        mock_schema_json_path.open = mock.mock_open(read_data="{}")

        with self.assertRaises(ValueError) as cm:
            call_command("generate_docs", "--check=true")
            self.assertIn("Api Schemas have changed and have not been updated", cm.value)
