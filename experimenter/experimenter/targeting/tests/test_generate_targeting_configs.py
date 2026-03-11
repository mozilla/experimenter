import json
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from experimenter.experiments.tests.factories import NimbusFeatureConfigFactory
from experimenter.targeting.constants import NimbusTargetingConfig


class TestGenerateTargetingConfigsCommand(TestCase):
    def test_generates_targeting_and_feature_configs(self):
        NimbusFeatureConfigFactory.create(slug="test-feature", enabled=True)

        with patch(
            "experimenter.base.management.commands.generate_targeting_configs.FIXTURES_DIR"
        ) as mock_dir:
            mock_dir.mkdir.return_value = None
            targeting_path = mock_dir.__truediv__.return_value
            targeting_path.write_text.return_value = None

            call_command("generate_targeting_configs")

            mock_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
            self.assertEqual(targeting_path.write_text.call_count, 2)

            targeting_json = targeting_path.write_text.call_args_list[0][0][0]
            targeting_configs = json.loads(targeting_json)
            self.assertEqual(
                len(targeting_configs), len(NimbusTargetingConfig.targeting_configs)
            )
            for config in targeting_configs:
                self.assertIn("label", config)
                self.assertIn("value", config)
                self.assertIn("applicationValues", config)
                self.assertIn("stickyRequired", config)
                self.assertIn("isFirstRunRequired", config)

            feature_json = targeting_path.write_text.call_args_list[1][0][0]
            feature_configs = json.loads(feature_json)
            self.assertTrue(len(feature_configs) > 0)
            for fc in feature_configs:
                self.assertIn("id", fc)
                self.assertIn("slug", fc)
                self.assertIn("application", fc)
