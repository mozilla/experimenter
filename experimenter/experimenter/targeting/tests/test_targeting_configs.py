import json

from django.test import TestCase
from parameterized import parameterized

from experimenter.experiments.constants import Application
from experimenter.experiments.jexl_utils import collect_exprs
from experimenter.experiments.tests.jexl_utils import validate_jexl_expr
from experimenter.targeting.constants import (
    PRESERVED_TARGETING_KEYS_BY_APPLICATION,
    TargetingConstants,
)
from experimenter.targeting.targeting_context_parser import TargetingContextFields


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

    @parameterized.expand([(t,) for t in TargetingConstants.TARGETING_CONFIGS.values()])
    def test_validate_targeting_config_fields(self, targeting_config):
        valid_fields = set()
        for app in targeting_config.application_choice_names:
            match app:
                case Application.DESKTOP.name:
                    valid_fields.update(
                        TargetingContextFields.for_application(Application.DESKTOP)
                    )
                    valid_fields.update(
                        PRESERVED_TARGETING_KEYS_BY_APPLICATION[Application.DESKTOP]
                    )
                case Application.FENIX.name:
                    valid_fields.update(
                        TargetingContextFields.for_application(Application.FENIX)
                    )
                    valid_fields.update(
                        PRESERVED_TARGETING_KEYS_BY_APPLICATION[Application.FENIX]
                    )
                case Application.IOS.name:
                    valid_fields.update(
                        TargetingContextFields.for_application(Application.IOS)
                    )
                    valid_fields.update(
                        PRESERVED_TARGETING_KEYS_BY_APPLICATION[Application.IOS]
                    )

        if targeting_config.targeting:
            extracted_root_fields = set()

            for subexpr in collect_exprs(targeting_config.targeting):
                try:
                    json.loads(subexpr)
                    continue
                except json.JSONDecodeError:
                    if subexpr.startswith("."):
                        continue
                    extracted_root_fields.add(subexpr.partition(".")[0])

            unknown_fields = extracted_root_fields - valid_fields

            self.assertFalse(
                unknown_fields,
                f"Unknown targeting fields in {targeting_config.slug}: {unknown_fields}",
            )
