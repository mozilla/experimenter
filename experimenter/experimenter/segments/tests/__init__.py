from pathlib import Path

from django.test import override_settings

mock_valid_segments = override_settings(
    METRIC_HUB_SEGMENTS_PATH_JETSTREAM=(
        Path(__file__).parent.absolute() / "fixtures" / "valid_segments_jetstream"
    ),
    METRIC_HUB_SEGMENTS_PATH_DEFAULT=(
        Path(__file__).parent.absolute() / "fixtures" / "valid_segments_default"
    ),
)

mock_invalid_segments = override_settings(
    METRIC_HUB_SEGMENTS_PATH_JETSTREAM=(
        Path(__file__).parent.absolute() / "fixtures" / "invalid_segments_jetstream"
    ),
    METRIC_HUB_SEGMENTS_PATH_DEFAULT=(
        Path(__file__).parent.absolute() / "fixtures" / "invalid_segments_default"
    ),
)
