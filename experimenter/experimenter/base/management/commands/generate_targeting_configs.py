import json
import logging
from pathlib import Path

from django.core.management.base import BaseCommand

from experimenter.targeting.constants import NimbusTargetingConfig

logger = logging.getLogger()

OUTPUT_PATH = (
    Path(__file__).resolve().parents[4]
    / "tests"
    / "integration"
    / "nimbus"
    / "fixtures"
    / "targeting_configs.json"
)


class Command(BaseCommand):
    help = "Generate targeting configs JSON for integration tests"

    def handle(self, *args, **options):
        configs = [
            {
                "label": config.name,
                "value": config.slug,
                "applicationValues": list(config.application_choice_names),
                "description": config.description,
                "stickyRequired": config.sticky_required,
                "isFirstRunRequired": config.is_first_run_required,
            }
            for config in NimbusTargetingConfig.targeting_configs
        ]

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(json.dumps(configs, indent=2) + "\n")

        logger.info(f"Generated {len(configs)} targeting configs to {OUTPUT_PATH}")
