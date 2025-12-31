from dataclasses import dataclass
from pathlib import Path

import toml
from django.conf import settings
from django.core.checks import Error, register


@dataclass
class Metric:
    slug: str
    friendly_name: str
    description: str
    metric_area: str = None
    application: str = None


class Metrics:
    _metrics = None

    @classmethod
    def _load_metrics(cls):
        metrics: list[Metric] = []

        metrics_path = settings.METRIC_HUB_SEGMENTS_PATH_DEFAULT / "definitions"
        metrics_dir = Path(metrics_path)

        for app_name in metrics_dir.iterdir():
            if app_name.suffix != ".toml":
                continue

            with app_name.open() as metric_file:
                metric_toml = metric_file.read()
                metric_data = toml.loads(metric_toml).get("metrics", {})

                for metric_slug, metric_key in metric_data.items():
                    metrics.append(
                        Metric(
                            description=metric_key.get("description"),
                            friendly_name=metric_key["friendly_name"],
                            slug=metric_slug,
                            metric_area=metric_key.get("metric_area"),
                            application=app_name.stem,
                        )
                    )

        return metrics

    @classmethod
    def clear_cache(cls):
        cls._metrics = None

    @classmethod
    def all(cls):
        if cls._metrics is None:
            cls._metrics = cls._load_metrics()

        return cls._metrics

    @classmethod
    def get_by_slug_and_application(cls, slug, application):
        for metric in cls.all():
            if metric.slug == slug and metric.application == application:
                return metric
        return None


@register()
def check_metrics_tomls(
    app_configs,
    **kwargs,
):
    errors = []

    try:
        Metrics.all()
    except Exception as e:
        errors.append(Error(f"Error loading Metric TOMLs: {e}"))
    return errors
