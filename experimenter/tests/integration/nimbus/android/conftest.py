import os
from pathlib import Path

import pytest


@pytest.fixture(name="fenix_channel")
def fixture_fenix_channel():
    value = os.environ.get("FENIX_CHANNEL")
    if not value:
        pytest.skip("FENIX_CHANNEL is not set")
    return value


@pytest.fixture(name="fenix_apk_path")
def fixture_fenix_apk_path():
    value = os.environ.get("FENIX_APK_PATH")
    if not value or not Path(value).exists():
        pytest.skip(f"FENIX_APK_PATH not set or missing: {value!r}")
    return value


@pytest.fixture
def experiment_slug(fenix_channel):
    return f"fenix-{fenix_channel}-integration-test"
