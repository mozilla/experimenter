import json

from django.core.management.base import BaseCommand

from experimenter.experiments.constants import (
    NIMBUS_TARGETING_CONTEXT_TABLE,
    Application,
)
from experimenter.experiments.jexl_to_sql import ensure_bool_sql, jexl_to_sql
from experimenter.targeting.constants import NimbusTargetingConfig


class Command(BaseCommand):
    help = "Export Desktop targeting SQL expressions for BigQuery dry-run validation"

    def handle(self, *args, **options):
        entries = []

        for config in NimbusTargetingConfig.targeting_configs:
            if Application.DESKTOP.name not in config.application_choice_names:
                continue
            if not config.targeting or config.targeting == "true":
                continue

            result = jexl_to_sql(config.targeting)
            if result.sql is None:
                continue

            sql = ensure_bool_sql(result.sql)
            query = (
                f"SELECT COUNTIF({sql})"
                f" FROM `{NIMBUS_TARGETING_CONTEXT_TABLE}`"
                " WHERE FALSE"
            )
            entries.append({"slug": config.slug, "query": query})

        json.dump(entries, self.stdout, indent=2)
        self.stdout.write("\n")
