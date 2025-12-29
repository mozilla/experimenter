from pathlib import Path

import toml
from django.conf import settings


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
