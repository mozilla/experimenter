from dataclasses import dataclass, field

from django.conf import settings
from django.core.checks import Error, register
from metric_config_parser.config import LocalConfigCollection, NimbusConfig
from metric_config_parser.nimbus import NimbusConfigKind

from experimenter.experiments.constants import NimbusConstants


@dataclass
class CatalogMetric:
    slug: str
    friendly_name: str
    description: str | None = None


@dataclass
class CatalogOutcome:
    slug: str
    metrics: list[str] = field(default_factory=list)


@dataclass
class ApplicationCatalog:
    application: str
    # Every metric the application declares, across its definitions, defaults and
    # outcome files. A metric is declared once, so the file it sits in only decides
    # how it is grouped.
    metrics: list[CatalogMetric] = field(default_factory=list)
    guardrails: list[str] = field(default_factory=list)
    outcomes: list[CatalogOutcome] = field(default_factory=list)


def _metric_names(config: NimbusConfig):
    return sorted(config.spec.metrics)


class Catalog:
    _catalogs = None

    @classmethod
    def _load_catalogs(cls, nimbus_configs: list[NimbusConfig] | None = None):
        if nimbus_configs is None:
            collection = LocalConfigCollection.from_local_path(
                path=settings.METRIC_HUB_NIMBUS_PATH, is_private=False
            )
            nimbus_configs = collection.nimbus_configs or []

        configs_by_app_name: dict[str, list[NimbusConfig]] = {}
        for config in nimbus_configs:
            configs_by_app_name.setdefault(config.app_name, []).append(config)

        catalogs = []
        for app_config in NimbusConstants.APPLICATION_CONFIGS.values():
            app_configs = configs_by_app_name.get(app_config.app_name, [])

            metrics = {}
            guardrails = []
            outcomes = []
            for config in app_configs:
                for name, metric in config.spec.metrics.items():
                    metrics[name] = CatalogMetric(
                        slug=name,
                        friendly_name=metric.friendly_name or name,
                        description=metric.description,
                    )
                if config.kind == NimbusConfigKind.DEFAULTS:
                    guardrails.extend(_metric_names(config))
                elif config.kind == NimbusConfigKind.OUTCOMES:
                    outcomes.append(
                        CatalogOutcome(slug=config.slug, metrics=_metric_names(config))
                    )

            catalogs.append(
                ApplicationCatalog(
                    application=app_config.slug,
                    metrics=[metrics[name] for name in sorted(metrics)],
                    guardrails=sorted(guardrails),
                    outcomes=sorted(outcomes, key=lambda outcome: outcome.slug),
                )
            )

        return catalogs

    @classmethod
    def clear_cache(cls):
        cls._catalogs = None

    @classmethod
    def all(cls, nimbus_configs: list[NimbusConfig] | None = None):
        if cls._catalogs is None:
            cls._catalogs = cls._load_catalogs(nimbus_configs)
        return cls._catalogs

    @classmethod
    def by_application(
        cls, application, nimbus_configs: list[NimbusConfig] | None = None
    ):
        for catalog in cls.all(nimbus_configs):
            if catalog.application == application:
                return catalog
        return ApplicationCatalog(application=application)


@register()
def check_catalog(app_configs, nimbus_configs=None, **kwargs):
    errors = []

    try:
        Catalog.all(nimbus_configs=nimbus_configs)
    except Exception as e:
        errors.append(Error(f"Error loading Catalog: {e}"))
    return errors
