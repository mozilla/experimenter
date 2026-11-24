from metric_config_parser.config import NimbusConfig
from metric_config_parser.metric import MetricDefinition
from metric_config_parser.nimbus import NimbusConfigKind, NimbusSpec


def nimbus_config(slug, app_name, kind, metrics):
    return NimbusConfig(
        slug=slug,
        app_name=app_name,
        spec=NimbusSpec(
            metrics={
                name: MetricDefinition(name=name, **fields)
                for name, fields in metrics.items()
            }
        ),
        kind=kind,
    )


def mock_nimbus_configs():
    return [
        nimbus_config(
            "firefox_desktop",
            "firefox_desktop",
            NimbusConfigKind.DEFINITIONS,
            {
                "uri_count": {
                    "friendly_name": "URIs visited",
                    "description": "URIs visited per client.",
                },
                "is_pinned": {"friendly_name": "Pinned to taskbar"},
            },
        ),
        nimbus_config(
            "firefox_desktop",
            "firefox_desktop",
            NimbusConfigKind.DEFAULTS,
            {
                "days_of_use": {"friendly_name": "Days of use"},
                "active_hours": {"friendly_name": "Active hours"},
            },
        ),
        nimbus_config(
            "onboarding",
            "firefox_desktop",
            NimbusConfigKind.OUTCOMES,
            {"first_run_retention": {"friendly_name": "First run retention"}},
        ),
        nimbus_config(
            "search",
            "firefox_desktop",
            NimbusConfigKind.OUTCOMES,
            {"search_count": {}, "ad_clicks": {}},
        ),
        nimbus_config(
            "fenix",
            "fenix",
            NimbusConfigKind.DEFINITIONS,
            {"fenix_uri_count": {"friendly_name": "URIs visited"}},
        ),
    ]
