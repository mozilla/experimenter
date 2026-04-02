from pathlib import Path

from django.test import override_settings

mock_targeting_manifests = override_settings(
    FEATURE_MANIFESTS_PATH=(Path(__file__).parent.absolute() / "mock-manifests"),
)
