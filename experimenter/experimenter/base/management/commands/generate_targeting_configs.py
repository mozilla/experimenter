import json
import logging
from pathlib import Path

from django.core.management.base import BaseCommand

from experimenter.experiments.constants import Application
from experimenter.experiments.models import NimbusFeatureConfig
from experimenter.targeting.constants import NimbusTargetingConfig

logger = logging.getLogger()

FIXTURES_DIR = (
    Path(__file__).resolve().parents[4] / "tests" / "integration" / "nimbus" / "fixtures"
)


class Command(BaseCommand):
    help = "Generate targeting and feature config JSON for integration tests"

    def handle(self, *args, **options):
        FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

        targeting_configs = [
            {
                "label": config.name,
                "value": config.slug,
                "applicationValues": [
                    Application[name].value for name in config.application_choice_names
                ],
                "description": config.description,
                "stickyRequired": config.sticky_required,
                "isFirstRunRequired": config.is_first_run_required,
            }
            for config in NimbusTargetingConfig.targeting_configs
        ]
        targeting_path = FIXTURES_DIR / "targeting_configs.json"
        targeting_path.write_text(f"{json.dumps(targeting_configs, indent=2)}\n")
        logger.info(
            f"Generated {len(targeting_configs)} targeting configs to {targeting_path}"
        )

        feature_configs = [
            {
                "id": fc.id,
                "slug": fc.slug,
                "application": fc.application,
            }
            for fc in NimbusFeatureConfig.objects.all().order_by("application", "slug")
        ]
        feature_path = FIXTURES_DIR / "feature_configs.json"
        feature_path.write_text(f"{json.dumps(feature_configs, indent=2)}\n")
        logger.info(f"Generated {len(feature_configs)} feature configs to {feature_path}")
