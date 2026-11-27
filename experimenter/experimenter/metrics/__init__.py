from dataclasses import dataclass, field
from pathlib import Path

import toml
from django.conf import settings
from django.core.checks import Error, register
from metric_config_parser.config import LocalConfigCollection, NimbusConfig
from metric_config_parser.nimbus import NimbusConfigKind

from experimenter.experiments.constants import NimbusConstants


class MetricAreas:
    _metric_areas = None

    @classmethod
    def _load_metrics_areas(cls):
        metric_areas = {}

        metrics_path = settings.METRIC_HUB_METRICS_PATH_DEFAULT
        metrics_dir = Path(metrics_path)

        for app_name in metrics_dir.iterdir():
            if app_name.suffix != ".toml":
                continue

            with app_name.open() as metric_file:
                metric_data = toml.load(metric_file).get("metrics", {}).get("areas")

                metric_areas[app_name.stem] = metric_data

        return metric_areas

    @classmethod
    def clear_cache(cls):
        cls._metric_areas = None

    @classmethod
    def all(cls):
        if cls._metric_areas is None:
            cls._metric_areas = cls._load_metrics_areas()

        return cls._metric_areas

    @classmethod
    def get(cls, application, slug):
        all_metrics = cls.all().get(application.replace("-", "_"))
        if all_metrics:
            for metric_area, slugs in all_metrics.items():
                if slug in slugs:
                    return metric_area.replace("_", " ").title()

        return None


@dataclass
class NimbusMetric:
    slug: str
    friendly_name: str
    description: str | None = None
    # How a unit's rows become one value. The results page reads this to tell a ratio,
    # which is reported with a headline rather than as a stack of windows alone.
    aggregation: str | None = None


@dataclass
class NimbusOutcome:
    slug: str
    metrics: list[str] = field(default_factory=list)


@dataclass
class ApplicationMetrics:
    application: str
    # Every metric the application declares, across its definitions, defaults and
    # outcome files. A metric is declared once, so the file it sits in only decides
    # how it is grouped.
    metrics: list[NimbusMetric] = field(default_factory=list)
    guardrails: list[str] = field(default_factory=list)
    outcomes: list[NimbusOutcome] = field(default_factory=list)


def _metric_names(config: NimbusConfig):
    return sorted(config.spec.metrics)


class NimbusMetrics:
    _application_metrics = None

    @classmethod
    def _load_application_metrics(cls, nimbus_configs: list[NimbusConfig] | None = None):
        if nimbus_configs is None:
            collection = LocalConfigCollection.from_local_path(
                path=settings.METRIC_HUB_NIMBUS_PATH, is_private=False
            )
            nimbus_configs = collection.nimbus_configs or []

        configs_by_app_name: dict[str, list[NimbusConfig]] = {}
        for config in nimbus_configs:
            configs_by_app_name.setdefault(config.app_name, []).append(config)

        application_metrics = []
        for app_config in NimbusConstants.APPLICATION_CONFIGS.values():
            app_configs = configs_by_app_name.get(app_config.app_name, [])

            metrics = {}
            guardrails = []
            outcomes = []
            for config in app_configs:
                for name, metric in config.spec.metrics.items():
                    metrics[name] = NimbusMetric(
                        slug=name,
                        friendly_name=metric.friendly_name or name,
                        description=metric.description,
                        aggregation=(
                            metric.aggregation.value if metric.aggregation else None
                        ),
                    )
                if config.kind == NimbusConfigKind.DEFAULTS:
                    guardrails.extend(_metric_names(config))
                elif config.kind == NimbusConfigKind.OUTCOMES:
                    outcomes.append(
                        NimbusOutcome(slug=config.slug, metrics=_metric_names(config))
                    )

            application_metrics.append(
                ApplicationMetrics(
                    application=app_config.slug,
                    metrics=[metrics[name] for name in sorted(metrics)],
                    guardrails=sorted(guardrails),
                    outcomes=sorted(outcomes, key=lambda outcome: outcome.slug),
                )
            )

        return application_metrics

    @classmethod
    def clear_cache(cls):
        cls._application_metrics = None

    @classmethod
    def all(cls, nimbus_configs: list[NimbusConfig] | None = None):
        if cls._application_metrics is None:
            cls._application_metrics = cls._load_application_metrics(nimbus_configs)
        return cls._application_metrics

    @classmethod
    def by_application(
        cls, application, nimbus_configs: list[NimbusConfig] | None = None
    ):
        for metrics in cls.all(nimbus_configs):
            if metrics.application == application:
                return metrics
        return ApplicationMetrics(application=application)


@register()
def check_nimbus_metrics(app_configs, nimbus_configs=None, **kwargs):
    errors = []

    try:
        NimbusMetrics.all(nimbus_configs=nimbus_configs)
    except Exception as e:
        errors.append(Error(f"Error loading NimbusMetrics: {e}"))
    return errors
