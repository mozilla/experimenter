from pathlib import Path

from django.test import override_settings

FIXTURES_PATH = Path(__file__).parent.absolute() / "fixtures" / "versions"

mock_valid_firefox_versions = override_settings(
    FIREFOX_VERSIONS_PATH=FIXTURES_PATH / "valid.yaml",
)

mock_firefox_versions_not_a_mapping = override_settings(
    FIREFOX_VERSIONS_PATH=FIXTURES_PATH / "not_a_mapping.yaml",
)

mock_firefox_versions_invalid_name = override_settings(
    FIREFOX_VERSIONS_PATH=FIXTURES_PATH / "invalid_name.yaml",
)

mock_firefox_versions_invalid_value_format = override_settings(
    FIREFOX_VERSIONS_PATH=FIXTURES_PATH / "invalid_value_format.yaml",
)

mock_firefox_versions_non_string_value = override_settings(
    FIREFOX_VERSIONS_PATH=FIXTURES_PATH / "non_string_value.yaml",
)

mock_firefox_versions_duplicate_value = override_settings(
    FIREFOX_VERSIONS_PATH=FIXTURES_PATH / "duplicate_value.yaml",
)
