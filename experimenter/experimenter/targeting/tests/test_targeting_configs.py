from django.test import TestCase
from parameterized import parameterized

from experimenter.experiments.constants import Application
from experimenter.experiments.tests.jexl_utils import validate_jexl_expr
from experimenter.targeting.constants import TargetingConstants


class TestTargetingConfigs(TestCase):
    def test_all_targeting_configs_defined_in_constants(self):
        self.assertEqual(
            {t.value for t in TargetingConstants.TargetingConfig},
            set(TargetingConstants.TARGETING_CONFIGS.keys()),
            "Targeting Configs must be defined in both "
            "TargetingConstants.TargetingConfig and TargetingConstants.TARGETING_CONFIGS",
        )

    @parameterized.expand([(t,) for t in TargetingConstants.TARGETING_CONFIGS.values()])
    def test_targeting_config_has_valid_jexl(self, targeting_config):
        if targeting_config.targeting:
            try:
                application = (
                    Application.DESKTOP
                    if Application.DESKTOP.name
                    in targeting_config.application_choice_names
                    else Application.FENIX
                )
                validate_jexl_expr(targeting_config.targeting, application)
            except Exception as e:
                raise Exception(
                    f"JEXL validation error in {targeting_config.name}: {e}"
                ) from e
