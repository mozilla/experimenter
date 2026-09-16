from pathlib import Path

from django.test import override_settings

FIXTURES_PATH = Path(__file__).parent.absolute() / "fixtures"

mock_valid_addon_versions = override_settings(
    ADDON_VERSIONS_PATH=FIXTURES_PATH / "valid_versions",
)

mock_invalid_addon_versions = override_settings(
    ADDON_VERSIONS_PATH=FIXTURES_PATH / "invalid_versions",
)

mock_multiple_addon_versions = override_settings(
    ADDON_VERSIONS_PATH=FIXTURES_PATH / "multiple_versions",
)

mock_missing_addon_versions = override_settings(
    ADDON_VERSIONS_PATH=FIXTURES_PATH / "no_such_versions",
)
