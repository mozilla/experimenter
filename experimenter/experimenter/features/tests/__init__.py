from pathlib import Path

from django.test import override_settings

FIXTURE_DIR = Path(__file__).parent.absolute() / "fixtures"

mock_valid_features = override_settings(
    FEATURE_MANIFESTS_PATH=FIXTURE_DIR / "valid_features"
)

mock_invalid_features = override_settings(
    FEATURE_MANIFESTS_PATH=FIXTURE_DIR / "invalid_features"
)

mock_remote_schema_features = override_settings(
    FEATURE_MANIFESTS_PATH=FIXTURE_DIR / "remote_schema_features"
)

mock_invalid_remote_schema_features = override_settings(
    FEATURE_MANIFESTS_PATH=FIXTURE_DIR / "invalid_remote_schema_features"
)

mock_versioned_features = override_settings(
    FEATURE_MANIFESTS_PATH=FIXTURE_DIR / "versioned_features"
)
