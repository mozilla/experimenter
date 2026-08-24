from django.test import TestCase
from parameterized import parameterized

from experimenter.experiments.constants import Application
from experimenter.experiments.jexl_to_sql import (
    JEXL_TO_BQ_COLUMN,
    KNOWN_UNTRANSLATABLE,
    jexl_to_sql,
)
from experimenter.experiments.jexl_utils import (
    extract_targeting_fields,
    extract_transform_names,
)
from experimenter.experiments.tests.jexl_utils import validate_jexl_expr
from experimenter.targeting.constants import (
    PRESERVED_TARGETING_KEYS_BY_APPLICATION,
    TRANSFORMS_BY_APPLICATION,
    TargetingConstants,
)
from experimenter.targeting.targeting_context_parser import TargetingContextFields


class TestTargetingConfigs(TestCase):
    def setUp(self):
        super().setUp()
        TargetingContextFields.clear_cache()

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
    def test_targeting_config_jexl_attributes_are_known(self, targeting_config):
        if not targeting_config.targeting or targeting_config.targeting == "true":
            return
        result = jexl_to_sql(targeting_config.targeting)
        for warning in result.warnings:
            if warning.startswith("|"):
                continue
            parts = warning.split(".")
            self.assertTrue(
                any(
                    ".".join(parts[:i]) in KNOWN_UNTRANSLATABLE
                    or warning in JEXL_TO_BQ_COLUMN
                    for i in range(1, len(parts) + 1)
                ),
                f"Unrecognized attribute '{warning}' in "
                f"{targeting_config.name}. Add it to "
                f"JEXL_TO_BQ_COLUMN or KNOWN_UNTRANSLATABLE.",
            )

    @parameterized.expand([(t,) for t in TargetingConstants.TARGETING_CONFIGS.values()])
    def test_targeting_config_transforms_are_known(self, targeting_config):
        if not targeting_config.targeting:
            return

        applications = [
            Application[app]
            for app in targeting_config.application_choice_names
            if Application[app] in TRANSFORMS_BY_APPLICATION
        ]

        for transform in extract_transform_names(targeting_config.targeting):
            for application in applications:
                self.assertIn(
                    transform,
                    TRANSFORMS_BY_APPLICATION[application],
                    f"Unknown JEXL transform '{transform}' in "
                    f"{targeting_config.slug} for {application.name}. "
                    f"Every transform must be supported by every application "
                    f"the config targets.",
                )

    def test_desktop_targeting_context_fields_are_mapped(self):
        """Every field in the Desktop targeting context must be in JEXL_TO_BQ_COLUMN
        or KNOWN_UNTRANSLATABLE.

        This test runs against the real (unversioned) Desktop targeting context file.
        When an Update External Configs PR adds a new field to the recorded targeting
        context, this test fails, requiring the SQL mapping to be updated in the same
        PR before the field can be referenced in any targeting config.
        """
        desktop_fields = TargetingContextFields.for_application(Application.DESKTOP)

        all_mapped_prefixes = {key.split(".")[0] for key in JEXL_TO_BQ_COLUMN} | set(
            JEXL_TO_BQ_COLUMN
        )
        all_untranslatable_prefixes = {
            key.split(".")[0] for key in KNOWN_UNTRANSLATABLE
        } | set(KNOWN_UNTRANSLATABLE)

        unmapped = [
            field
            for field in desktop_fields
            if field not in all_mapped_prefixes
            and field not in all_untranslatable_prefixes
        ]

        self.assertFalse(
            unmapped,
            f"Desktop targeting context fields not covered by JEXL_TO_BQ_COLUMN "
            f"or KNOWN_UNTRANSLATABLE: {unmapped}. "
            f"Add a mapping in jexl_to_sql.py or add to KNOWN_UNTRANSLATABLE.",
        )

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
            unknown_fields = (
                extract_targeting_fields(targeting_config.targeting) - valid_fields
            )

            self.assertFalse(
                unknown_fields,
                f"Unknown targeting fields in {targeting_config.slug}: {unknown_fields}",
            )
