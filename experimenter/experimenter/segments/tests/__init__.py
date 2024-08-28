from pathlib import Path

from django.test import override_settings

mock_valid_segments = override_settings(
    JETSTREAM_CONFIG_SEGMENTS_PATH=(
        Path(__file__).parent.absolute() / "fixtures" / "valid_segments"
    ),
    DEFINITIONS_CONFIG_SEGMENTS_PATH=(
        Path(__file__).parent.absolute() / "fixtures" / "valid_segments_definitions"
    ),
)

mock_invalid_segments = override_settings(
    JETSTREAM_CONFIG_SEGMENTS_PATH=(
        Path(__file__).parent.absolute() / "fixtures" / "invalid_segments"
    ),
    DEFINITIONS_CONFIG_SEGMENTS_PATH=(
        Path(__file__).parent.absolute() / "fixtures" / "invalid_segments_definitions"
    ),
)
