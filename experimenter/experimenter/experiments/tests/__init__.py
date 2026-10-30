from pathlib import Path

from django.test import override_settings

FIXTURES_PATH = Path(__file__).parent.absolute() / "fixtures" / "versions"
MANIFEST_FIXTURES_PATH = Path(__file__).parent.absolute() / "fixtures" / "manifests"

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

mock_manifests_same_major = override_settings(
    FEATURE_MANIFESTS_PATH=MANIFEST_FIXTURES_PATH / "same_major",
)

mock_manifests_fenix_ahead = override_settings(
    FEATURE_MANIFESTS_PATH=MANIFEST_FIXTURES_PATH / "fenix_ahead",
)

mock_manifests_non_version_dir = override_settings(
    FEATURE_MANIFESTS_PATH=MANIFEST_FIXTURES_PATH / "non_version_dir",
)
