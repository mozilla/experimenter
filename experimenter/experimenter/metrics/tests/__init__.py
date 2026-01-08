from pathlib import Path

from django.test import override_settings

mock_valid_metrics = override_settings(
    METRIC_HUB_METRICS_PATH_DEFAULT=(
        Path(__file__).parent.absolute() / "mock_metrics" / "valid_metrics"
    ),
)
