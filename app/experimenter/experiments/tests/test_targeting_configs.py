from django.test import TestCase
from parameterized import parameterized
from parsimonious.exceptions import ParseError
from pyjexl.jexl import JEXLConfig
from pyjexl.operators import default_binary_operators, default_unary_operators
from pyjexl.parser import Parser, jexl_grammar

from experimenter.experiments.constants import NimbusConstants

default_config = JEXLConfig({}, default_unary_operators, default_binary_operators)


class DefaultParser(Parser):
    grammar = jexl_grammar(default_config)

    def __init__(self):
        super().__init__(default_config)


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
                DefaultParser().parse(targeting_config.targeting)
            except ParseError as e:
                raise Exception(f"JEXL Parse error in {targeting_config.name}: {e}")
