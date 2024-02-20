from pathlib import Path

from django.test import override_settings

mock_valid_outcomes = override_settings(
    JETSTREAM_CONFIG_OUTCOMES_PATH=(
        Path(__file__).parent.absolute() / "fixtures" / "valid_outcomes"
    ),
)
