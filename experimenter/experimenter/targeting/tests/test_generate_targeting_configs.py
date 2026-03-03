import json
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from experimenter.targeting.constants import NimbusTargetingConfig


class TestGenerateTargetingConfigsCommand(TestCase):
    def test_generates_json_file(self):
        with patch(
            "experimenter.base.management.commands.generate_targeting_configs.OUTPUT_PATH"
        ) as mock_path:
            mock_path.parent.mkdir.return_value = None

            call_command("generate_targeting_configs")

            mock_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
            mock_path.write_text.assert_called_once()

            written_json = mock_path.write_text.call_args[0][0]
            configs = json.loads(written_json)

            self.assertEqual(len(configs), len(NimbusTargetingConfig.targeting_configs))

            for config in configs:
                self.assertIn("label", config)
                self.assertIn("value", config)
                self.assertIn("applicationValues", config)
                self.assertIn("description", config)
                self.assertIn("stickyRequired", config)
                self.assertIn("isFirstRunRequired", config)

            first = configs[0]
            source = NimbusTargetingConfig.targeting_configs[0]
            self.assertEqual(first["label"], source.name)
            self.assertEqual(first["value"], source.slug)
            self.assertEqual(
                first["applicationValues"], list(source.application_choice_names)
            )
            self.assertEqual(first["stickyRequired"], source.sticky_required)
            self.assertEqual(first["isFirstRunRequired"], source.is_first_run_required)
