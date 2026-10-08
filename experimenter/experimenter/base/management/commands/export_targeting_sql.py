import json

from django.core.management.base import BaseCommand

from experimenter.experiments.constants import (
    NIMBUS_TARGETING_CONTEXT_TABLE,
    NIMBUS_TARGETING_CONTEXT_TABLE_FENIX,
    NIMBUS_TARGETING_CONTEXT_TABLE_IOS,
    TARGETING_SQL_DRY_RUN_TEMPLATE,
    TARGETING_SQL_DRY_RUN_TEMPLATE_MOBILE,
    Application,
)
from experimenter.experiments.jexl_to_sql import (
    APP_NAME_TO_JEXL_APP,
    ensure_bool_sql,
    jexl_to_sql,
)
from experimenter.targeting.constants import NimbusTargetingConfig

_APP_CONFIG = {
    "desktop": (Application.DESKTOP, NIMBUS_TARGETING_CONTEXT_TABLE, None),
    "fenix": (
        Application.FENIX,
        NIMBUS_TARGETING_CONTEXT_TABLE_FENIX,
        APP_NAME_TO_JEXL_APP["fenix"],
    ),
    "ios": (
        Application.IOS,
        NIMBUS_TARGETING_CONTEXT_TABLE_IOS,
        APP_NAME_TO_JEXL_APP["firefox_ios"],
    ),
}


class Command(BaseCommand):
    help = "Export targeting SQL expressions for BigQuery dry-run validation"

    def add_arguments(self, parser):
        parser.add_argument(
            "--app",
            choices=list(_APP_CONFIG.keys()),
            default="desktop",
            help="Application to export targeting SQL for (default: desktop)",
        )

    def handle(self, *args, **options):
        app_key = options["app"]
        application, table, jexl_app = _APP_CONFIG[app_key]

        entries = []
        for config in NimbusTargetingConfig.targeting_configs:
            if application.name not in config.application_choice_names:
                continue
            if not config.targeting or config.targeting == "true":
                continue

            result = jexl_to_sql(config.targeting, app=jexl_app)
            if result.sql is None:
                continue

            sql = ensure_bool_sql(result.sql)
            # Mobile attributes resolve out of the nested context blob, so the
            # dry-run needs the same projection the sizing pool applies.
            template = (
                TARGETING_SQL_DRY_RUN_TEMPLATE
                if jexl_app is None
                else TARGETING_SQL_DRY_RUN_TEMPLATE_MOBILE
            )
            query = template.format(predicate=sql, table=table)
            entries.append(
                {
                    "slug": config.slug,
                    "query": query,
                    "warnings": result.warnings,
                }
            )

        json.dump(entries, self.stdout, indent=2)
        self.stdout.write("\n")
