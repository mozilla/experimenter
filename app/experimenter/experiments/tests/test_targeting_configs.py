from django.test import TestCase
from parameterized import parameterized
from parsimonious.exceptions import ParseError

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.tests import JEXLParser


class TestTargetingConfigs(TestCase):
    def test_all_targeting_configs_defined_in_constants(self):
        self.assertEqual(
            set([t.value for t in NimbusConstants.TargetingConfig]),
            set(t for t in NimbusConstants.TARGETING_CONFIGS.keys()),
            "Targeting Configs must be defined in both NimbusConstants.TargetingConfig "
            "and NimbusConstants.TARGETING_CONFIGS",
        )

    @parameterized.expand([(t,) for t in NimbusConstants.TARGETING_CONFIGS.values()])
    def test_targeting_config_has_valid_jexl(self, targeting_config):
        if targeting_config.targeting:
            try:
                JEXLParser().parse(targeting_config.targeting)
            except ParseError as e:
                raise Exception(f"JEXL Parse error in {targeting_config.name}: {e}")
